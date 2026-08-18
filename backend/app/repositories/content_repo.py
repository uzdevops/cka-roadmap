"""Phase / Week / Lesson / Lab persistence.

Everything a student sees belongs to exactly one track, so `track_id` is a
required argument rather than an optional filter. That is deliberate: a missed
filter here does not raise, it quietly returns another certification's content,
or counts it into somebody's progress. A required parameter turns that into a
TypeError the moment a call site is missed.

Lookups by slug are the exception. Lesson, lab and quiz slugs stay globally
unique (that is what keeps the 85-file translation corpus addressable), so those
cannot collide across tracks and do not need the filter to be correct.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Lab, LabProgress, Lesson, LessonProgress, Phase, Week


# --- Phases --------------------------------------------------------------


async def list_phases(session: AsyncSession, track_id: int) -> list[Phase]:
    stmt = (
        select(Phase).where(Phase.track_id == track_id).order_by(Phase.order_index)
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_phase_by_slug(
    session: AsyncSession, track_id: int, slug: str
) -> Phase | None:
    """Phase slugs are unique per track, so both are needed.

    Without the track this is a `scalar_one_or_none` over several rows once a
    second track has a phase called "foundations" - a 500, not a 404.
    """
    stmt = (
        select(Phase)
        .where(Phase.track_id == track_id, Phase.slug == slug)
        .options(selectinload(Phase.weeks).selectinload(Week.lessons))
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_phase_by_id(session: AsyncSession, phase_id: int) -> Phase | None:
    return await session.get(Phase, phase_id)


async def get_roadmap(session: AsyncSession, track_id: int) -> list[Phase]:
    stmt = (
        select(Phase)
        .where(Phase.track_id == track_id)
        .options(selectinload(Phase.weeks).selectinload(Week.lessons))
        .order_by(Phase.order_index)
    )
    return list((await session.execute(stmt)).scalars().unique().all())


# --- Weeks ---------------------------------------------------------------


async def get_week_by_number(
    session: AsyncSession, track_id: int, number: int
) -> Week | None:
    """Week numbers restart at 1 in every track - the number alone is ambiguous."""
    stmt = (
        select(Week)
        .where(Week.track_id == track_id, Week.number == number)
        .options(selectinload(Week.lessons), selectinload(Week.phase))
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def list_weeks(session: AsyncSession, track_id: int) -> list[Week]:
    stmt = select(Week).where(Week.track_id == track_id).order_by(Week.number)
    return list((await session.execute(stmt)).scalars().all())


# --- Lessons -------------------------------------------------------------


async def get_lesson_by_slug(session: AsyncSession, slug: str) -> Lesson | None:
    """Lesson slugs are globally unique, so this needs no track."""
    stmt = (
        select(Lesson)
        .where(Lesson.slug == slug)
        .options(selectinload(Lesson.week).selectinload(Week.phase))
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_lesson_by_id(session: AsyncSession, lesson_id: int) -> Lesson | None:
    return await session.get(Lesson, lesson_id)


async def list_lessons_ordered(session: AsyncSession, track_id: int) -> list[Lesson]:
    """Every published lesson of one track, in curriculum order.

    This is what prev/next indexes into. Unscoped, the last lesson of one track
    hands the reader the first lesson of the next one.
    """
    stmt = (
        select(Lesson)
        .join(Week, Lesson.week_id == Week.id)
        .join(Phase, Week.phase_id == Phase.id)
        .where(Lesson.is_published.is_(True), Phase.track_id == track_id)
        .order_by(Phase.order_index, Week.number, Lesson.order_index, Lesson.id)
    )
    return list((await session.execute(stmt)).scalars().all())


async def count_lessons(session: AsyncSession, track_id: int) -> int:
    """Needs the joins: `lessons` carries no track of its own."""
    stmt = (
        select(func.count(Lesson.id))
        .select_from(Lesson)
        .join(Week, Lesson.week_id == Week.id)
        .where(Lesson.is_published.is_(True), Week.track_id == track_id)
    )
    return int((await session.execute(stmt)).scalar_one())


async def completed_lesson_ids(
    session: AsyncSession, user_id: int, track_id: int | None = None
) -> set[int]:
    """Ids only, so an unscoped set is still safe to look up against.

    `track_id` is optional here precisely because the result is used as a
    membership test, never as a total.
    """
    stmt = select(LessonProgress.lesson_id).where(
        LessonProgress.user_id == user_id, LessonProgress.completed.is_(True)
    )
    if track_id is not None:
        stmt = (
            stmt.join(Lesson, LessonProgress.lesson_id == Lesson.id)
            .join(Week, Lesson.week_id == Week.id)
            .where(Week.track_id == track_id)
        )
    return set((await session.execute(stmt)).scalars().all())


async def get_lesson_progress(
    session: AsyncSession, user_id: int, lesson_id: int
) -> LessonProgress | None:
    stmt = select(LessonProgress).where(
        LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def completed_lessons_per_phase(
    session: AsyncSession, user_id: int, track_id: int
) -> dict[int, int]:
    stmt = (
        select(Phase.id, func.count(LessonProgress.id))
        .select_from(LessonProgress)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .join(Week, Lesson.week_id == Week.id)
        .join(Phase, Week.phase_id == Phase.id)
        .where(
            LessonProgress.user_id == user_id,
            LessonProgress.completed.is_(True),
            Phase.track_id == track_id,
        )
        .group_by(Phase.id)
    )
    return {pid: count for pid, count in (await session.execute(stmt)).all()}


async def total_lessons_per_phase(
    session: AsyncSession, track_id: int
) -> dict[int, int]:
    stmt = (
        select(Phase.id, func.count(Lesson.id))
        .select_from(Phase)
        .join(Week, Week.phase_id == Phase.id)
        .join(Lesson, Lesson.week_id == Week.id)
        .where(Lesson.is_published.is_(True), Phase.track_id == track_id)
        .group_by(Phase.id)
    )
    return {pid: count for pid, count in (await session.execute(stmt)).all()}


# --- Labs ----------------------------------------------------------------


async def list_labs(
    session: AsyncSession, track_id: int, phase_slug: str | None = None
) -> list[Lab]:
    stmt = (
        select(Lab)
        .join(Phase, Lab.phase_id == Phase.id)
        .options(selectinload(Lab.phase))
        .where(Lab.is_published.is_(True), Phase.track_id == track_id)
        .order_by(Phase.order_index, Lab.order_index, Lab.id)
    )
    if phase_slug:
        stmt = stmt.where(Phase.slug == phase_slug)
    return list((await session.execute(stmt)).scalars().all())


async def get_lab_by_slug(session: AsyncSession, slug: str) -> Lab | None:
    """Lab slugs are globally unique, so this needs no track."""
    stmt = select(Lab).where(Lab.slug == slug).options(selectinload(Lab.phase))
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_lab_progress(
    session: AsyncSession, user_id: int, lab_id: int
) -> LabProgress | None:
    stmt = select(LabProgress).where(
        LabProgress.user_id == user_id, LabProgress.lab_id == lab_id
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def lab_progress_map(session: AsyncSession, user_id: int) -> dict[int, str]:
    stmt = select(LabProgress.lab_id, LabProgress.status).where(
        LabProgress.user_id == user_id
    )
    return {lab_id: status for lab_id, status in (await session.execute(stmt)).all()}


async def count_labs(session: AsyncSession, track_id: int) -> int:
    """Needs the join: `labs` reaches its track through its phase."""
    stmt = (
        select(func.count(Lab.id))
        .select_from(Lab)
        .join(Phase, Lab.phase_id == Phase.id)
        .where(Lab.is_published.is_(True), Phase.track_id == track_id)
    )
    return int((await session.execute(stmt)).scalar_one())
