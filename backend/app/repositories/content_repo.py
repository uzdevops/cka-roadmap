"""Phase / Week / Lesson / Lab persistence."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Lab, LabProgress, Lesson, LessonProgress, Phase, Week


# --- Phases --------------------------------------------------------------


async def list_phases(session: AsyncSession) -> list[Phase]:
    stmt = select(Phase).order_by(Phase.order_index)
    return list((await session.execute(stmt)).scalars().all())


async def get_phase_by_slug(session: AsyncSession, slug: str) -> Phase | None:
    stmt = (
        select(Phase)
        .where(Phase.slug == slug)
        .options(selectinload(Phase.weeks).selectinload(Week.lessons))
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_phase_by_id(session: AsyncSession, phase_id: int) -> Phase | None:
    return await session.get(Phase, phase_id)


async def get_roadmap(session: AsyncSession) -> list[Phase]:
    stmt = (
        select(Phase)
        .options(selectinload(Phase.weeks).selectinload(Week.lessons))
        .order_by(Phase.order_index)
    )
    return list((await session.execute(stmt)).scalars().unique().all())


# --- Weeks ---------------------------------------------------------------


async def get_week_by_number(session: AsyncSession, number: int) -> Week | None:
    stmt = (
        select(Week)
        .where(Week.number == number)
        .options(selectinload(Week.lessons), selectinload(Week.phase))
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def list_weeks(session: AsyncSession) -> list[Week]:
    stmt = select(Week).order_by(Week.number)
    return list((await session.execute(stmt)).scalars().all())


# --- Lessons -------------------------------------------------------------


async def get_lesson_by_slug(session: AsyncSession, slug: str) -> Lesson | None:
    stmt = (
        select(Lesson)
        .where(Lesson.slug == slug)
        .options(selectinload(Lesson.week).selectinload(Week.phase))
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_lesson_by_id(session: AsyncSession, lesson_id: int) -> Lesson | None:
    return await session.get(Lesson, lesson_id)


async def list_lessons_ordered(session: AsyncSession) -> list[Lesson]:
    """Every published lesson in curriculum order (used for prev/next + sitemap)."""
    stmt = (
        select(Lesson)
        .join(Week, Lesson.week_id == Week.id)
        .join(Phase, Week.phase_id == Phase.id)
        .where(Lesson.is_published.is_(True))
        .order_by(Phase.order_index, Week.number, Lesson.order_index, Lesson.id)
    )
    return list((await session.execute(stmt)).scalars().all())


async def count_lessons(session: AsyncSession) -> int:
    stmt = select(func.count(Lesson.id)).where(Lesson.is_published.is_(True))
    return int((await session.execute(stmt)).scalar_one())


async def completed_lesson_ids(session: AsyncSession, user_id: int) -> set[int]:
    stmt = select(LessonProgress.lesson_id).where(
        LessonProgress.user_id == user_id, LessonProgress.completed.is_(True)
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
    session: AsyncSession, user_id: int
) -> dict[int, int]:
    stmt = (
        select(Phase.id, func.count(LessonProgress.id))
        .select_from(LessonProgress)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .join(Week, Lesson.week_id == Week.id)
        .join(Phase, Week.phase_id == Phase.id)
        .where(LessonProgress.user_id == user_id, LessonProgress.completed.is_(True))
        .group_by(Phase.id)
    )
    return {pid: count for pid, count in (await session.execute(stmt)).all()}


async def total_lessons_per_phase(session: AsyncSession) -> dict[int, int]:
    stmt = (
        select(Phase.id, func.count(Lesson.id))
        .select_from(Phase)
        .join(Week, Week.phase_id == Phase.id)
        .join(Lesson, Lesson.week_id == Week.id)
        .where(Lesson.is_published.is_(True))
        .group_by(Phase.id)
    )
    return {pid: count for pid, count in (await session.execute(stmt)).all()}


# --- Labs ----------------------------------------------------------------


async def list_labs(session: AsyncSession, phase_slug: str | None = None) -> list[Lab]:
    stmt = (
        select(Lab)
        .join(Phase, Lab.phase_id == Phase.id)
        .options(selectinload(Lab.phase))
        .where(Lab.is_published.is_(True))
        .order_by(Phase.order_index, Lab.order_index, Lab.id)
    )
    if phase_slug:
        stmt = stmt.where(Phase.slug == phase_slug)
    return list((await session.execute(stmt)).scalars().all())


async def get_lab_by_slug(session: AsyncSession, slug: str) -> Lab | None:
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


async def count_labs(session: AsyncSession) -> int:
    stmt = select(func.count(Lab.id)).where(Lab.is_published.is_(True))
    return int((await session.execute(stmt)).scalar_one())
