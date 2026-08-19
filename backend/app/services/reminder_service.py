"""The 20:30 nudge: who gets one, about what, and what the answer does.

No new content model. "Today's task" is derived from the roadmap the person is
already following - their current week, and the lessons that week places on this
weekday - so the reminder cannot describe a plan that differs from the one on
the site.

The selection lives here and is shared with the bot's `/today`, deliberately:
a message that says two lessons are due and a command that says three would make
both untrustworthy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import (
    Lesson,
    LessonProgress,
    ReminderKind,
    ReminderLog,
    Track,
    TrackEnrollment,
    User,
    Week,
)
from app.services import enrollment_service

# Saturday is the lab day and Sunday is review. Neither is a lesson day, and a
# nudge about lessons on a day that has none is noise - so the reminder simply
# does not run at the weekend.
LESSON_DAYS = {1, 2, 3, 4, 5}


@dataclass
class DueToday:
    """One track's unfinished lessons for today."""

    track: Track
    enrollment: TrackEnrollment
    week_number: int
    lessons: list[Lesson] = field(default_factory=list)


def is_lesson_day(when: date) -> bool:
    return when.isoweekday() in LESSON_DAYS


async def due_today(
    session: AsyncSession, user: User, when: date | None = None
) -> list[DueToday]:
    """Lessons this person was meant to do today and has NOT finished.

    Already-finished lessons drop out here rather than at the message: somebody
    who did the work should hear nothing at all, and filtering later would still
    have sent them a message listing zero items.
    """
    day = when or datetime.now(UTC).date()
    if not is_lesson_day(day):
        return []

    enrollments = (
        await session.execute(
            select(TrackEnrollment).where(
                TrackEnrollment.user_id == user.id,
                TrackEnrollment.status == "active",
            )
        )
    ).scalars().all()

    completed = set(
        (
            await session.execute(
                select(LessonProgress.lesson_id).where(
                    LessonProgress.user_id == user.id,
                    LessonProgress.completed.is_(True),
                )
            )
        ).scalars().all()
    )

    out: list[DueToday] = []
    for enrollment in enrollments:
        track = await session.get(Track, enrollment.track_id)
        if track is None:
            continue

        week_number = enrollment_service.expected_week(enrollment.started_at, on=day)
        total = await enrollment_service.duration_weeks(session, track)
        if total and week_number > total:
            # The roadmap has run out. Nothing is "due" past the end of it.
            continue

        lessons = (
            await session.execute(
                select(Lesson)
                .join(Week, Lesson.week_id == Week.id)
                .where(
                    Week.track_id == track.id,
                    Week.number == week_number,
                    Lesson.is_published.is_(True),
                    Lesson.day_of_week == day.isoweekday(),
                )
                .order_by(Lesson.order_index, Lesson.id)
            )
        ).scalars().all()

        outstanding = [lesson for lesson in lessons if lesson.id not in completed]
        if outstanding:
            out.append(
                DueToday(
                    track=track,
                    enrollment=enrollment,
                    week_number=week_number,
                    lessons=outstanding,
                )
            )
    return out


async def claim_reminder(
    session: AsyncSession,
    user: User,
    track: Track,
    lessons: list[Lesson],
    when: date,
) -> ReminderLog | None:
    """Reserve today's send, or discover somebody already did.

    Returns None when a reminder for this person, day and kind already exists.
    The check is an INSERT ... ON CONFLICT DO NOTHING rather than a SELECT then
    an INSERT: two bot processes, or one restarted mid-send, would both pass a
    SELECT and both send. The database is the only place that can arbitrate
    that, which is why the uniqueness lives there.
    """
    stmt = (
        pg_insert(ReminderLog)
        .values(
            user_id=user.id,
            track_id=track.id,
            reminder_date=when,
            kind=ReminderKind.DAILY_TASK,
            lesson_ids=[lesson.id for lesson in lessons],
            sent_at=datetime.now(UTC),
        )
        .on_conflict_do_nothing(
            index_elements=["user_id", "reminder_date", "kind"]
        )
        .returning(ReminderLog.id)
    )
    reminder_id = (await session.execute(stmt)).scalar_one_or_none()
    if reminder_id is None:
        return None
    await session.commit()
    return await session.get(ReminderLog, reminder_id)


async def record_answer(
    session: AsyncSession, reminder: ReminderLog, answer: str
) -> None:
    reminder.answer = answer
    reminder.answered_at = datetime.now(UTC)
    await session.commit()


async def audience(session: AsyncSession) -> list[User]:
    """Everyone who could receive a reminder: linked, active, and studying.

    The enrollment join is what keeps a message from going to somebody who
    connected the bot and then never started a track.
    """
    stmt = (
        select(User)
        .join(TrackEnrollment, TrackEnrollment.user_id == User.id)
        .where(
            User.telegram_chat_id.is_not(None),
            User.is_active.is_(True),
            TrackEnrollment.status == "active",
        )
        .distinct()
    )
    return list((await session.execute(stmt)).scalars().all())


@dataclass(frozen=True)
class Lateness:
    """The numbers the "No" reply uses.

    Real figures, from the same service the dashboard reads - a motivational
    line with an invented number is worse than no line at all.
    """

    days_behind: int
    actual_week: int
    expected_week: int


async def lateness(
    session: AsyncSession, user: User, track: Track
) -> Lateness:
    state = await enrollment_service.describe(session, user, track)
    return Lateness(
        days_behind=max(0, state.behind_by_weeks * 7),
        actual_week=state.actual_week,
        expected_week=state.expected_week,
    )


def lesson_url(track_slug: str, quiz_slug: str) -> str:
    """Where to send somebody whose lesson still needs its quiz."""
    base = (settings.frontend_origin or "").rstrip("/")
    return f"{base}/en/{track_slug}/quizzes/{quiz_slug}"
