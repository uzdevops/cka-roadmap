"""Lesson reading and completion."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentUser, Locale, SessionDep
from app.i18n import has_translation, tr
from app.repositories import content_repo, progress_repo
from app.schemas.content import (
    LessonCompleteResponse,
    LessonDetail,
    LessonSummary,
)
from app.services.progress_service import compute_streaks

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("", response_model=list[LessonSummary])
async def list_lessons(
    session: SessionDep, user: CurrentUser, locale: Locale
) -> list[LessonSummary]:
    lessons = await content_repo.list_lessons_ordered(session)
    done = await content_repo.completed_lesson_ids(session, user.id) if user else set()
    return [
        LessonSummary(
            id=lsn.id,
            slug=lsn.slug,
            title=tr(lsn, "title", locale),
            summary=tr(lsn, "summary", locale),
            order_index=lsn.order_index,
            estimated_minutes=lsn.estimated_minutes,
            day_of_week=lsn.day_of_week,
            is_placeholder=lsn.is_placeholder,
            completed=lsn.id in done,
        )
        for lsn in lessons
    ]


@router.get("/{slug}", response_model=LessonDetail)
async def get_lesson(
    slug: str, session: SessionDep, user: CurrentUser, locale: Locale
) -> LessonDetail:
    lesson = await content_repo.get_lesson_by_slug(session, slug)
    if lesson is None or not lesson.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )

    ordered = await content_repo.list_lessons_ordered(session)
    slugs = [lsn.slug for lsn in ordered]
    try:
        idx = slugs.index(slug)
    except ValueError:
        idx = -1
    prev_slug = slugs[idx - 1] if idx > 0 else None
    next_slug = slugs[idx + 1] if 0 <= idx < len(slugs) - 1 else None

    done = await content_repo.completed_lesson_ids(session, user.id) if user else set()

    return LessonDetail(
        id=lesson.id,
        slug=lesson.slug,
        title=tr(lesson, "title", locale),
        summary=tr(lesson, "summary", locale),
        content=tr(lesson, "content", locale),
        content_translated=has_translation(lesson, "content", locale),
        order_index=lesson.order_index,
        estimated_minutes=lesson.estimated_minutes,
        day_of_week=lesson.day_of_week,
        is_placeholder=lesson.is_placeholder,
        completed=lesson.id in done,
        week_id=lesson.week_id,
        week_number=lesson.week.number if lesson.week else None,
        week_title=tr(lesson.week, "title", locale) if lesson.week else None,
        phase_slug=lesson.week.phase.slug if lesson.week and lesson.week.phase else None,
        phase_title=(
            tr(lesson.week.phase, "title", locale)
            if lesson.week and lesson.week.phase
            else None
        ),
        prev_slug=prev_slug,
        next_slug=next_slug,
    )


async def _set_completion(
    session, user, slug: str, completed: bool
) -> LessonCompleteResponse:
    lesson = await content_repo.get_lesson_by_slug(session, slug)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )
    await progress_repo.set_lesson_completed(session, user.id, lesson.id, completed)
    if completed:
        await progress_repo.record_activity(session, user.id)
    await session.commit()

    streak = compute_streaks(await progress_repo.activity_days(session, user.id))
    return LessonCompleteResponse(
        lesson_id=lesson.id, completed=completed, streak=streak.current_streak
    )


@router.post("/{slug}/complete", response_model=LessonCompleteResponse)
async def complete_lesson(
    slug: str, session: SessionDep, user: CurrentUser
) -> LessonCompleteResponse:
    return await _set_completion(session, user, slug, True)


@router.delete("/{slug}/complete", response_model=LessonCompleteResponse)
async def uncomplete_lesson(
    slug: str, session: SessionDep, user: CurrentUser
) -> LessonCompleteResponse:
    return await _set_completion(session, user, slug, False)
