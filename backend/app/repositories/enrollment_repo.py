"""Track enrollment persistence."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Lesson,
    LessonProgress,
    Phase,
    TrackEnrollment,
    Week,
)


async def get(
    session: AsyncSession, user_id: int, track_id: int
) -> TrackEnrollment | None:
    stmt = select(TrackEnrollment).where(
        TrackEnrollment.user_id == user_id, TrackEnrollment.track_id == track_id
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def list_for_user(session: AsyncSession, user_id: int) -> list[TrackEnrollment]:
    stmt = select(TrackEnrollment).where(TrackEnrollment.user_id == user_id)
    return list((await session.execute(stmt)).scalars().all())


async def map_for_user(
    session: AsyncSession, user_id: int
) -> dict[int, TrackEnrollment]:
    """Keyed by track id, for decorating a list of tracks in one round trip."""
    return {e.track_id: e for e in await list_for_user(session, user_id)}


async def add(session: AsyncSession, enrollment: TrackEnrollment) -> TrackEnrollment:
    session.add(enrollment)
    await session.flush()
    return enrollment


async def max_week_end(session: AsyncSession, track_id: int) -> int:
    """The last week number the track's phases describe.

    Zero when the track has phases but none of them set `week_end` - the caller
    falls back to counting weeks, then to a default.
    """
    stmt = select(func.coalesce(func.max(Phase.week_end), 0)).where(
        Phase.track_id == track_id
    )
    return int((await session.execute(stmt)).scalar_one() or 0)


async def count_weeks(session: AsyncSession, track_id: int) -> int:
    stmt = select(func.count(Week.id)).where(Week.track_id == track_id)
    return int((await session.execute(stmt)).scalar_one() or 0)


async def furthest_completed_week(
    session: AsyncSession, user_id: int, track_id: int
) -> int:
    """The highest week number this user has completed a lesson in.

    Used as "where they actually are", against "where the calendar says they
    should be". Deliberately the furthest rather than a count of completions: a
    person who finished week 6 is in week 6 even if they skipped a lesson in
    week 3.
    """
    stmt = (
        select(func.coalesce(func.max(Week.number), 0))
        .select_from(LessonProgress)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .join(Week, Lesson.week_id == Week.id)
        .where(
            LessonProgress.user_id == user_id,
            LessonProgress.completed.is_(True),
            Week.track_id == track_id,
        )
    )
    return int((await session.execute(stmt)).scalar_one() or 0)


async def content_counts(session: AsyncSession, track_id: int) -> dict[str, int]:
    """Lessons and weeks in a track, for the "what am I signing up for" screen."""
    lessons = (
        await session.execute(
            select(func.count(Lesson.id))
            .select_from(Lesson)
            .join(Week, Lesson.week_id == Week.id)
            .where(Lesson.is_published.is_(True), Week.track_id == track_id)
        )
    ).scalar_one()
    return {
        "lessons": int(lessons or 0),
        "weeks": await count_weeks(session, track_id),
    }
