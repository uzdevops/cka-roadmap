"""Assembles the roadmap tree and decorates it with per-user progress."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Lesson, Phase, Track, User, Week
from app.i18n import DEFAULT_LOCALE, SUNDAY_REVIEW, tr, weekday
from app.repositories import content_repo
from app.schemas.content import (
    LessonSummary,
    PhaseDetail,
    PhaseSummary,
    WeeklySchedule,
    WeeklyScheduleDay,
    WeekRead,
)
from app.services import quiz_service

def _lesson_summary(
    lesson: Lesson, done: set[int], locale: str = DEFAULT_LOCALE
) -> LessonSummary:
    return LessonSummary(
        id=lesson.id,
        slug=lesson.slug,
        title=tr(lesson, "title", locale),
        summary=tr(lesson, "summary", locale),
        order_index=lesson.order_index,
        estimated_minutes=lesson.estimated_minutes,
        day_of_week=lesson.day_of_week,
        is_placeholder=lesson.is_placeholder,
        completed=lesson.id in done,
    )


def _week_read(week: Week, done: set[int], locale: str = DEFAULT_LOCALE) -> WeekRead:
    lessons = [
        _lesson_summary(lsn, done, locale)
        for lsn in sorted(week.lessons, key=lambda x: (x.order_index, x.id))
        if lsn.is_published
    ]
    return WeekRead(
        id=week.id,
        number=week.number,
        title=tr(week, "title", locale),
        description=tr(week, "description", locale),
        order_index=week.order_index,
        lessons=lessons,
        completed_lessons=sum(1 for lsn in lessons if lsn.completed),
        total_lessons=len(lessons),
    )


def _phase_summary(
    phase: Phase, total: int, completed: int, locked: bool,
    locale: str = DEFAULT_LOCALE,
) -> PhaseSummary:
    return PhaseSummary(
        id=phase.id,
        slug=phase.slug,
        title=tr(phase, "title", locale),
        description=tr(phase, "description", locale),
        order_index=phase.order_index,
        exam_domain=tr(phase, "exam_domain", locale),
        exam_weight=phase.exam_weight,
        week_start=phase.week_start,
        week_end=phase.week_end,
        color=phase.color,
        total_lessons=total,
        completed_lessons=completed,
        progress_percent=round((completed / total) * 100, 1) if total else 0.0,
        locked=locked,
    )


async def list_phases(
    session: AsyncSession, track: Track, user: User | None,
    locale: str = DEFAULT_LOCALE,
) -> list[PhaseSummary]:
    phases = await content_repo.list_phases(session, track.id)
    totals = await content_repo.total_lessons_per_phase(session, track.id)
    completed = (
        await content_repo.completed_lessons_per_phase(session, user.id, track.id)
        if user
        else {}
    )
    locked = await quiz_service.locked_phase_ids(session, user, track.id)
    return [
        _phase_summary(
            p, totals.get(p.id, 0), completed.get(p.id, 0), p.id in locked, locale
        )
        for p in phases
    ]


async def get_phase(
    session: AsyncSession, track: Track, slug: str, user: User | None,
    locale: str = DEFAULT_LOCALE,
) -> PhaseDetail | None:
    phase = await content_repo.get_phase_by_slug(session, track.id, slug)
    if phase is None:
        return None

    done = await content_repo.completed_lesson_ids(session, user.id) if user else set()
    weeks = [
        _week_read(w, done, locale)
        for w in sorted(phase.weeks, key=lambda x: x.order_index)
    ]
    total = sum(w.total_lessons for w in weeks)
    completed = sum(w.completed_lessons for w in weeks)
    locked = await quiz_service.locked_phase_ids(session, user, track.id)

    base = _phase_summary(phase, total, completed, phase.id in locked, locale)
    return PhaseDetail(**base.model_dump(), weeks=weeks, quizzes=[], labs=[])


async def get_roadmap(
    session: AsyncSession, track: Track, user: User | None,
    locale: str = DEFAULT_LOCALE,
) -> list[PhaseDetail]:
    phases = await content_repo.get_roadmap(session, track.id)
    done = await content_repo.completed_lesson_ids(session, user.id) if user else set()
    locked = await quiz_service.locked_phase_ids(session, user, track.id)

    out: list[PhaseDetail] = []
    for phase in phases:
        weeks = [
            _week_read(w, done, locale)
            for w in sorted(phase.weeks, key=lambda x: x.order_index)
        ]
        total = sum(w.total_lessons for w in weeks)
        completed = sum(w.completed_lessons for w in weeks)
        base = _phase_summary(phase, total, completed, phase.id in locked, locale)
        out.append(PhaseDetail(**base.model_dump(), weeks=weeks, quizzes=[], labs=[]))
    return out


async def weekly_schedule(
    session: AsyncSession, track: Track, week_number: int, user: User | None,
    locale: str = DEFAULT_LOCALE,
) -> WeeklySchedule | None:
    """Mon-Fri lessons, Saturday lab day, Sunday review."""
    week = await content_repo.get_week_by_number(session, track.id, week_number)
    if week is None:
        return None

    done = await content_repo.completed_lesson_ids(session, user.id) if user else set()
    labs = await content_repo.list_labs(session, track.id)
    week_labs = [lab for lab in labs if lab.week_id == week.id]

    days: list[WeeklyScheduleDay] = []
    lessons = sorted(
        (lsn for lsn in week.lessons if lsn.is_published),
        key=lambda x: (x.order_index, x.id),
    )

    for day in range(1, 6):
        items = [
            _lesson_summary(lsn, done, locale).model_dump()
            for lsn in lessons
            if (lsn.day_of_week or ((lsn.order_index % 5) + 1)) == day
        ]
        days.append(
            WeeklyScheduleDay(
                day=day, label=weekday(day, locale), kind="lesson", items=items
            )
        )

    days.append(
        WeeklyScheduleDay(
            day=6,
            label=weekday(6, locale),
            kind="lab",
            items=[
                {"id": lab.id, "slug": lab.slug,
                 "title": tr(lab, "title", locale),
                 "estimated_minutes": lab.estimated_minutes}
                for lab in week_labs
            ],
        )
    )
    days.append(
        WeeklyScheduleDay(
            day=7,
            label=weekday(7, locale),
            kind="review",
            items=[{"title": SUNDAY_REVIEW.get(locale, SUNDAY_REVIEW["en"])}],
        )
    )

    return WeeklySchedule(
        week_number=week.number,
        week_title=tr(week, "title", locale),
        phase_slug=week.phase.slug,
        days=days,
    )
