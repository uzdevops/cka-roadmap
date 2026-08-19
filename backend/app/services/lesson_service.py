"""Finishing a lesson - the one implementation of it.

The web button and the Telegram button both come through here. Before this
existed the rule lived inside `routers/lessons.py`, and the bot writing to
`lesson_progress` directly would have skipped the quiz gate, the study streak
and the activity record that phase unlocking counts - three things that only
look correct until somebody checks.

The rule itself is unchanged: a lesson that has a quiz is completed by passing
that quiz, never by pressing a button.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lesson, Quiz, User
from app.repositories import progress_repo, quiz_repo


class LessonGated(Exception):
    """Raised when a lesson can only be finished by passing its quiz.

    Carries the quiz so the caller can point at it - a refusal that does not say
    where to go next is just a dead end.
    """

    def __init__(self, quiz: Quiz) -> None:
        super().__init__("This lesson is completed by passing its quiz")
        self.quiz = quiz


@dataclass(frozen=True)
class CompletionResult:
    lesson_id: int
    completed: bool
    read_only: bool
    quiz_slug: str | None = None
    quiz_pass_score: float | None = None


async def gate_for(session: AsyncSession, user: User, lesson: Lesson) -> Quiz | None:
    """The quiz standing between this user and finishing the lesson, if any.

    Returns None when there is no quiz, or when it has already been passed -
    both cases mean the lesson may be completed directly.
    """
    quiz = await quiz_repo.get_lesson_quiz(session, lesson.id)
    if quiz is None:
        return None
    best, _ = await quiz_repo.attempt_stats_for_quiz(session, user.id, quiz.id)
    if best is not None and best >= quiz.pass_score:
        return None
    return quiz


async def set_completion(
    session: AsyncSession, user: User, lesson: Lesson, completed: bool
) -> None:
    """The raw write, plus the activity record.

    `record_activity` is not optional bookkeeping: the study streak and the
    phase-unlock calculation both read it, so writing progress without it
    produces a user whose streak silently stops counting.
    """
    await progress_repo.set_lesson_completed(session, user.id, lesson.id, completed)
    if completed:
        await progress_repo.record_activity(session, user.id)


async def mark_read(
    session: AsyncSession, user: User, lesson: Lesson, source: str
) -> None:
    """Read, but not finished.

    What "Yes" means for a lesson whose quiz is still outstanding. It is
    deliberately visible in the UI - somebody who said yes and saw no progress
    move would otherwise assume the button was broken.
    """
    row = await progress_repo.set_lesson_completed(
        session, user.id, lesson.id, completed=False
    )
    # Only ever set, never cleared here: the first time somebody says they read
    # it is the interesting one.
    if row.read_at is None:
        row.read_at = datetime.now(UTC)
        row.read_source = source
    await session.flush()


async def complete(
    session: AsyncSession, user: User, lesson: Lesson, source: str = "web"
) -> CompletionResult:
    """Finish a lesson, or explain why it cannot be finished this way.

    Raises `LessonGated` when a quiz is outstanding. Callers that must not fail -
    the Telegram button - catch it and fall back to `mark_read`; the web router
    turns it into a 409, which is the behaviour it already had.
    """
    quiz = await gate_for(session, user, lesson)
    if quiz is not None:
        raise LessonGated(quiz)

    await set_completion(session, user, lesson, completed=True)
    return CompletionResult(lesson_id=lesson.id, completed=True, read_only=False)


async def complete_or_mark_read(
    session: AsyncSession, user: User, lesson: Lesson, source: str
) -> CompletionResult:
    """What a "Yes" in Telegram does.

    A lesson with no outstanding quiz is finished exactly as the web button
    finishes it. One with a quiz is recorded as read and the quiz is handed
    back, so the reply can say what is still needed instead of silently doing
    less than the user expected.
    """
    try:
        return await complete(session, user, lesson, source=source)
    except LessonGated as gated:
        await mark_read(session, user, lesson, source=source)
        return CompletionResult(
            lesson_id=lesson.id,
            completed=False,
            read_only=True,
            quiz_slug=gated.quiz.slug,
            quiz_pass_score=gated.quiz.pass_score,
        )
