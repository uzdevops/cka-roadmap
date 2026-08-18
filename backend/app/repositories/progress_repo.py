"""Lesson/lab progress and study-activity persistence."""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Lab,
    LabProgress,
    Lesson,
    LessonProgress,
    Phase,
    StudyActivity,
    Week,
)


async def set_lesson_completed(
    session: AsyncSession, user_id: int, lesson_id: int, completed: bool
) -> LessonProgress:
    stmt = select(LessonProgress).where(
        LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    now = datetime.now(UTC)
    if row is None:
        row = LessonProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            completed=completed,
            completed_at=now if completed else None,
        )
        session.add(row)
    else:
        row.completed = completed
        row.completed_at = now if completed else None
    await session.flush()
    return row


async def set_lab_status(
    session: AsyncSession, user_id: int, lab_id: int, status: str
) -> LabProgress:
    stmt = select(LabProgress).where(
        LabProgress.user_id == user_id, LabProgress.lab_id == lab_id
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    completed_at = datetime.now(UTC) if status == "completed" else None
    if row is None:
        row = LabProgress(
            user_id=user_id, lab_id=lab_id, status=status, completed_at=completed_at
        )
        session.add(row)
    else:
        row.status = status
        row.completed_at = completed_at
    await session.flush()
    return row


async def record_activity(
    session: AsyncSession, user_id: int, when: date | None = None
) -> None:
    """Idempotent per (user, day); bumps an event counter on repeat activity."""
    day = when or datetime.now(UTC).date()
    stmt = (
        pg_insert(StudyActivity)
        .values(user_id=user_id, activity_date=day, events=1)
        .on_conflict_do_update(
            index_elements=[StudyActivity.user_id, StudyActivity.activity_date],
            set_={"events": StudyActivity.events + 1},
        )
    )
    await session.execute(stmt)


async def activity_days(session: AsyncSession, user_id: int) -> list[date]:
    stmt = (
        select(StudyActivity.activity_date)
        .where(StudyActivity.user_id == user_id)
        .order_by(StudyActivity.activity_date)
    )
    return list((await session.execute(stmt)).scalars().all())


async def count_completed_lessons(
    session: AsyncSession, user_id: int, track_id: int
) -> int:
    """Joined through week, so a lesson finished in another track is not counted
    against this track's total - which would push completion over 100%."""
    stmt = (
        select(func.count(LessonProgress.id))
        .select_from(LessonProgress)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .join(Week, Lesson.week_id == Week.id)
        .where(
            LessonProgress.user_id == user_id,
            LessonProgress.completed.is_(True),
            Week.track_id == track_id,
        )
    )
    return int((await session.execute(stmt)).scalar_one())


async def count_completed_labs(
    session: AsyncSession, user_id: int, track_id: int
) -> int:
    stmt = (
        select(func.count(LabProgress.id))
        .select_from(LabProgress)
        .join(Lab, LabProgress.lab_id == Lab.id)
        .join(Phase, Lab.phase_id == Phase.id)
        .where(
            LabProgress.user_id == user_id,
            LabProgress.status == "completed",
            Phase.track_id == track_id,
        )
    )
    return int((await session.execute(stmt)).scalar_one())


async def count_all_completed_lessons(session: AsyncSession) -> int:
    stmt = select(func.count(LessonProgress.id)).where(
        LessonProgress.completed.is_(True)
    )
    return int((await session.execute(stmt)).scalar_one())
