"""Quiz / question / attempt persistence."""

from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Phase, Question, Quiz, QuizAttempt


async def list_quizzes(
    session: AsyncSession,
    phase_slug: str | None = None,
    *,
    track_id: int | None = None,
    published_only: bool = True,
    standalone_only: bool = True,
) -> list[Quiz]:
    """Quizzes, filtered for whoever is asking.

    The defaults are the student view: published quizzes that are not bound to a
    lesson. A quiz with a `lesson_id` is that lesson's gate and is taken from
    inside the lesson; listing it on the roadmap as well would put the same
    questions in two places and make a phase look like it has sixty quizzes
    instead of two.

    Both filters are arguments rather than baked in because the admin panel has
    to see and edit every quiz - with them hardcoded it could reach only 20 of
    the 78 that exist, and the other 58 were uneditable with nothing to say so.

    The join is an outer join: `phase_id` is nullable, and a quiz with no phase
    should still be visible to an admin who has to go and fix it.
    """
    stmt = (
        select(Quiz)
        .outerjoin(Phase, Quiz.phase_id == Phase.id)
        .options(selectinload(Quiz.questions), selectinload(Quiz.phase))
        .order_by(Phase.order_index, Quiz.order_index, Quiz.id)
    )
    if track_id is not None:
        stmt = stmt.where(Phase.track_id == track_id)
    if published_only:
        stmt = stmt.where(Quiz.is_published.is_(True))
    if standalone_only:
        stmt = stmt.where(Quiz.lesson_id.is_(None))
    if phase_slug:
        stmt = stmt.where(Phase.slug == phase_slug)
    return list((await session.execute(stmt)).scalars().unique().all())


async def get_quiz_by_slug(session: AsyncSession, slug: str) -> Quiz | None:
    stmt = (
        select(Quiz)
        .where(Quiz.slug == slug)
        .options(selectinload(Quiz.questions), selectinload(Quiz.phase))
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_quiz_by_id(session: AsyncSession, quiz_id: int) -> Quiz | None:
    stmt = (
        select(Quiz)
        .where(Quiz.id == quiz_id)
        .options(selectinload(Quiz.questions), selectinload(Quiz.phase))
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def add_attempt(session: AsyncSession, attempt: QuizAttempt) -> QuizAttempt:
    session.add(attempt)
    await session.flush()
    return attempt


async def list_attempts(
    session: AsyncSession, user_id: int, limit: int = 50
) -> list[QuizAttempt]:
    stmt = (
        select(QuizAttempt)
        .where(QuizAttempt.user_id == user_id)
        .options(selectinload(QuizAttempt.quiz))
        .order_by(desc(QuizAttempt.created_at))
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().unique().all())


async def best_scores(session: AsyncSession, user_id: int) -> dict[int, float]:
    stmt = (
        select(QuizAttempt.quiz_id, func.max(QuizAttempt.score))
        .where(QuizAttempt.user_id == user_id)
        .group_by(QuizAttempt.quiz_id)
    )
    return {qid: float(score) for qid, score in (await session.execute(stmt)).all()}


async def attempt_counts(session: AsyncSession, user_id: int) -> dict[int, int]:
    stmt = (
        select(QuizAttempt.quiz_id, func.count(QuizAttempt.id))
        .where(QuizAttempt.user_id == user_id)
        .group_by(QuizAttempt.quiz_id)
    )
    return {qid: int(count) for qid, count in (await session.execute(stmt)).all()}


async def best_score_per_phase(
    session: AsyncSession, user_id: int, track_id: int
) -> dict[int, float]:
    """Average of the best score per quiz, grouped by phase, within one track."""
    best = (
        select(
            Quiz.phase_id.label("phase_id"),
            QuizAttempt.quiz_id.label("quiz_id"),
            func.max(QuizAttempt.score).label("best"),
        )
        .select_from(QuizAttempt)
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .join(Phase, Quiz.phase_id == Phase.id)
        .where(QuizAttempt.user_id == user_id, Phase.track_id == track_id)
        .group_by(Quiz.phase_id, QuizAttempt.quiz_id)
        .subquery()
    )
    stmt = select(best.c.phase_id, func.avg(best.c.best)).group_by(best.c.phase_id)
    return {pid: float(avg) for pid, avg in (await session.execute(stmt)).all()}


async def count_quizzes(session: AsyncSession, track_id: int) -> int:
    """Reaches its track through the phase - `quizzes` has no track of its own."""
    stmt = (
        select(func.count(Quiz.id))
        .select_from(Quiz)
        .join(Phase, Quiz.phase_id == Phase.id)
        .where(Quiz.is_published.is_(True), Phase.track_id == track_id)
    )
    return int((await session.execute(stmt)).scalar_one())


async def count_quizzes_by_track(session: AsyncSession) -> dict[int, int]:
    """Every track's quiz count in one query, for the all-tracks grid."""
    stmt = (
        select(Phase.track_id, func.count(Quiz.id))
        .select_from(Quiz)
        .join(Phase, Quiz.phase_id == Phase.id)
        .where(Quiz.is_published.is_(True))
        .group_by(Phase.track_id)
    )
    return {track_id: int(n) for track_id, n in (await session.execute(stmt)).all()}


async def count_questions(session: AsyncSession) -> int:
    return int((await session.execute(select(func.count(Question.id)))).scalar_one())


async def get_lesson_quiz(session: AsyncSession, lesson_id: int) -> Quiz | None:
    """The published quiz that gates a lesson, if one has been written yet."""
    stmt = (
        select(Quiz)
        .where(Quiz.lesson_id == lesson_id, Quiz.is_published.is_(True))
        .order_by(Quiz.order_index, Quiz.id)
        .options(selectinload(Quiz.questions))
        .limit(1)
    )
    return (await session.execute(stmt)).scalars().first()


async def attempt_stats_for_quiz(
    session: AsyncSession, user_id: int, quiz_id: int
) -> tuple[float | None, int]:
    """(best score, attempt count) for one user on one quiz."""
    stmt = select(
        func.max(QuizAttempt.score), func.count(QuizAttempt.id)
    ).where(QuizAttempt.user_id == user_id, QuizAttempt.quiz_id == quiz_id)
    best, count = (await session.execute(stmt)).one()
    return (float(best) if best is not None else None, int(count or 0))
