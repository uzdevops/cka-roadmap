"""The 20:30 nudge: selection, idempotency, and what the buttons may do.

No network anywhere. The selection and the answers are exercised through the
service layer, and the callback handler runs against a fake query object - the
same arrangement test_telegram_link.py uses.

The most important tests here guard one rule: the Telegram "Yes" button must not
be able to finish a lesson the website would refuse to finish. The quiz gate is
the platform's central promise, and a button in a chat is the easiest place to
accidentally break it.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Lesson,
    LessonProgress,
    Phase,
    Question,
    Quiz,
    ReminderLog,
    StudyActivity,
    Track,
    TrackEnrollment,
    User,
    Week,
)
from app.services import lesson_service, reminder_service

# A Wednesday and the weekend around it, so weekday logic is explicit.
WEDNESDAY = date(2026, 8, 19)
SATURDAY = date(2026, 8, 22)
SUNDAY = date(2026, 8, 23)


async def _track_with_week(
    session: AsyncSession, student: User, *, weeks_ago: int = 0
) -> tuple[Track, list[Lesson]]:
    """One track, enrolled, with lessons on Wednesday of the current week."""
    track = Track(slug="cka", title="CKA", is_topic=True, order_index=0)
    session.add(track)
    await session.flush()

    phase = Phase(
        track_id=track.id, slug="foundations", title="Phase", description="",
        order_index=1, exam_weight=10, week_start=1, week_end=20,
    )
    session.add(phase)
    await session.flush()

    week_number = weeks_ago + 1
    week = Week(
        track_id=track.id, phase_id=phase.id, number=week_number,
        title=f"Week {week_number}", description="", order_index=week_number,
    )
    session.add(week)
    await session.flush()

    lessons = []
    for i, day in enumerate((3, 3)):  # two lessons on Wednesday
        lesson = Lesson(
            week_id=week.id, slug=f"wed-lesson-{i}", title=f"Wednesday lesson {i}",
            summary="", content="body", order_index=i, estimated_minutes=30,
            day_of_week=day, is_published=True, is_placeholder=False,
        )
        session.add(lesson)
        lessons.append(lesson)
    await session.flush()

    started = datetime.combine(
        WEDNESDAY - timedelta(weeks=weeks_ago, days=2), datetime.min.time(), UTC
    )
    session.add(
        TrackEnrollment(
            user_id=student.id, track_id=track.id, started_at=started,
            auto_target_date=WEDNESDAY + timedelta(weeks=20),
            target_date=WEDNESDAY + timedelta(weeks=20),
            target_source="auto", status="active",
        )
    )
    await session.commit()
    return track, lessons


def _gate(session_lessons: list[Lesson]):
    """Attach a quiz to the first lesson, so it is completed only by passing."""
    lesson = session_lessons[0]
    return lesson


# --- selection ---------------------------------------------------------------


async def test_todays_selection_matches_the_week_and_weekday(
    session: AsyncSession, student_user: User
) -> None:
    track, lessons = await _track_with_week(session, student_user)

    due = await reminder_service.due_today(session, student_user, when=WEDNESDAY)
    assert len(due) == 1
    assert due[0].week_number == 1
    assert {l.id for l in due[0].lessons} == {l.id for l in lessons}


@pytest.mark.parametrize("day", [SATURDAY, SUNDAY], ids=["saturday", "sunday"])
async def test_no_selection_at_the_weekend(
    session: AsyncSession, student_user: User, day: date
) -> None:
    """Saturday is the lab day and Sunday is review; a lesson nudge on either is
    noise, so the whole selection is empty."""
    await _track_with_week(session, student_user)
    assert await reminder_service.due_today(session, student_user, when=day) == []


async def test_finished_lessons_drop_out(
    session: AsyncSession, student_user: User
) -> None:
    track, lessons = await _track_with_week(session, student_user)
    session.add(
        LessonProgress(
            user_id=student_user.id, lesson_id=lessons[0].id, completed=True
        )
    )
    await session.commit()

    due = await reminder_service.due_today(session, student_user, when=WEDNESDAY)
    assert [l.id for l in due[0].lessons] == [lessons[1].id]


async def test_nothing_due_means_no_reminder_at_all(
    session: AsyncSession, student_user: User
) -> None:
    """Somebody who did the work hears nothing. Silence is the reward."""
    track, lessons = await _track_with_week(session, student_user)
    for lesson in lessons:
        session.add(
            LessonProgress(
                user_id=student_user.id, lesson_id=lesson.id, completed=True
            )
        )
    await session.commit()

    assert await reminder_service.due_today(session, student_user, when=WEDNESDAY) == []


# --- idempotency -------------------------------------------------------------


async def test_a_restarted_bot_cannot_send_twice(
    session: AsyncSession, student_user: User
) -> None:
    """The guarantee is the UNIQUE constraint, not a memory of having sent.

    Claiming twice for the same person and day is exactly what a bot restarted
    at 20:31 would do; the second claim must come back empty-handed.
    """
    track, lessons = await _track_with_week(session, student_user)

    first = await reminder_service.claim_reminder(
        session, student_user, track, lessons, WEDNESDAY
    )
    assert first is not None

    second = await reminder_service.claim_reminder(
        session, student_user, track, lessons, WEDNESDAY
    )
    assert second is None, "the same day must not be claimable twice"

    rows = (
        await session.execute(
            select(ReminderLog).where(ReminderLog.user_id == student_user.id)
        )
    ).scalars().all()
    assert len(rows) == 1


# --- what "Yes" may do -------------------------------------------------------


async def test_yes_completes_a_lesson_with_no_quiz(
    session: AsyncSession, student_user: User
) -> None:
    """Identical to the web button, activity record included - the streak and
    phase unlocking both count it."""
    track, lessons = await _track_with_week(session, student_user)

    result = await lesson_service.complete_or_mark_read(
        session, student_user, lessons[0], source="telegram"
    )
    await session.commit()

    assert result.completed is True and result.read_only is False

    progress = (
        await session.execute(
            select(LessonProgress).where(
                LessonProgress.user_id == student_user.id,
                LessonProgress.lesson_id == lessons[0].id,
            )
        )
    ).scalar_one()
    assert progress.completed is True

    activity = (
        await session.execute(
            select(StudyActivity).where(StudyActivity.user_id == student_user.id)
        )
    ).scalars().all()
    assert activity, "completing must record a study day, or the streak dies"


async def test_yes_cannot_bypass_the_quiz_gate(
    session: AsyncSession, student_user: User
) -> None:
    """THE test of this PR. A gated lesson answered "Yes" becomes READ, not
    completed, and the caller is told which quiz still stands."""
    track, lessons = await _track_with_week(session, student_user)
    quiz = Quiz(
        phase_id=(await session.get(Week, lessons[0].week_id)).phase_id,
        week_id=lessons[0].week_id, lesson_id=lessons[0].id,
        slug="wed-check", title="Check", description="",
        pass_score=90.0, order_index=0, is_published=True,
    )
    session.add(quiz)
    await session.flush()
    session.add(
        Question(
            quiz_id=quiz.id, key="q1", type="single_choice", prompt="?",
            options=[{"id": "a", "text": "a"}], correct_options=["a"],
            accepted_answers=[], explanation="", order_index=0, points=1,
        )
    )
    await session.commit()

    result = await lesson_service.complete_or_mark_read(
        session, student_user, lessons[0], source="telegram"
    )
    await session.commit()

    assert result.completed is False
    assert result.read_only is True
    assert result.quiz_slug == "wed-check"

    progress = (
        await session.execute(
            select(LessonProgress).where(
                LessonProgress.user_id == student_user.id,
                LessonProgress.lesson_id == lessons[0].id,
            )
        )
    ).scalar_one()
    assert progress.completed is False, "the gate held"
    assert progress.read_at is not None
    assert progress.read_source == "telegram"


async def test_the_web_gate_is_unchanged(
    session: AsyncSession, student_user: User
) -> None:
    """The refactor moved the gate into a service; the web behaviour must be
    byte-for-byte what test_lesson_quiz_gate.py already pins. This is a direct
    check that the service raises where the router used to 409."""
    track, lessons = await _track_with_week(session, student_user)
    quiz = Quiz(
        phase_id=(await session.get(Week, lessons[0].week_id)).phase_id,
        week_id=lessons[0].week_id, lesson_id=lessons[0].id,
        slug="gate-check", title="Check", description="",
        pass_score=90.0, order_index=0, is_published=True,
    )
    session.add(quiz)
    await session.commit()

    with pytest.raises(lesson_service.LessonGated):
        await lesson_service.complete(session, student_user, lessons[0])


# --- the callback handler ----------------------------------------------------


def _query(data: str):
    q = SimpleNamespace(
        data=data,
        answer=AsyncMock(),
        edit_message_text=AsyncMock(),
        message=SimpleNamespace(reply_text=AsyncMock()),
    )
    return SimpleNamespace(callback_query=q), q


class _Factory:
    def __init__(self, session):
        self._session = session

    def __call__(self):
        return self

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, *exc):
        return False


async def test_no_keeps_the_task_open_and_records_the_answer(
    session: AsyncSession, student_user: User
) -> None:
    from app.bot import reminders

    track, lessons = await _track_with_week(session, student_user)
    reminder = await reminder_service.claim_reminder(
        session, student_user, track, lessons, WEDNESDAY
    )

    update, q = _query(f"r:{reminder.id}:n")
    with patch.object(reminders, "SessionLocal", _Factory(session)):
        await reminders.on_answer(update, SimpleNamespace())

    await session.refresh(reminder)
    assert reminder.answer == "no"
    assert reminder.answered_at is not None

    progress = (
        await session.execute(
            select(LessonProgress).where(LessonProgress.user_id == student_user.id)
        )
    ).scalars().all()
    assert all(not p.completed for p in progress), "No must not complete anything"

    said = q.edit_message_text.await_args.kwargs.get("text") or (
        q.edit_message_text.await_args.args[0] if q.edit_message_text.await_args.args else ""
    )
    # A real number, not a platitude.
    assert "weeks done" in said


async def test_yes_through_the_handler_marks_and_confirms(
    session: AsyncSession, student_user: User
) -> None:
    from app.bot import reminders

    track, lessons = await _track_with_week(session, student_user)
    reminder = await reminder_service.claim_reminder(
        session, student_user, track, lessons, WEDNESDAY
    )

    update, q = _query(f"r:{reminder.id}:y")
    with patch.object(reminders, "SessionLocal", _Factory(session)):
        await reminders.on_answer(update, SimpleNamespace())

    await session.refresh(reminder)
    assert reminder.answer == "yes"

    done = (
        await session.execute(
            select(LessonProgress).where(
                LessonProgress.user_id == student_user.id,
                LessonProgress.completed.is_(True),
            )
        )
    ).scalars().all()
    assert len(done) == len(lessons), "All done should complete every listed lesson"


async def test_a_stale_callback_is_polite_not_an_error(
    session: AsyncSession, student_user: User
) -> None:
    from app.bot import reminders

    update, q = _query("r:999999:y")
    with patch.object(reminders, "SessionLocal", _Factory(session)):
        await reminders.on_answer(update, SimpleNamespace())

    said = q.edit_message_text.await_args.kwargs.get("text") or (
        q.edit_message_text.await_args.args[0] if q.edit_message_text.await_args.args else ""
    )
    assert "expired" in said.lower()
