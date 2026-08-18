"""Lesson reading and completion."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentUser, Locale, SessionDep, StartedTrack
from app.i18n import has_translation, tr
from app.repositories import content_repo, progress_repo, quiz_repo
from app.schemas.content import (
    LessonCompleteResponse,
    LessonDetail,
    LessonSummary,
)
from app.services.progress_service import compute_streaks

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("", response_model=list[LessonSummary])
async def list_lessons(
    session: SessionDep, track: StartedTrack, user: CurrentUser, locale: Locale
) -> list[LessonSummary]:
    lessons = await content_repo.list_lessons_ordered(session, track.id)
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
    slug: str, session: SessionDep, track: StartedTrack, user: CurrentUser,
    locale: Locale,
) -> LessonDetail:
    lesson = await content_repo.get_lesson_by_slug(session, slug)
    if lesson is None or not lesson.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )

    # Scoped, so prev/next cannot walk out of this track and hand the reader
    # the first lesson of another one.
    ordered = await content_repo.list_lessons_ordered(session, track.id)
    slugs = [lsn.slug for lsn in ordered]
    try:
        idx = slugs.index(slug)
    except ValueError:
        idx = -1
    prev_slug = slugs[idx - 1] if idx > 0 else None
    next_slug = slugs[idx + 1] if 0 <= idx < len(slugs) - 1 else None

    done = await content_repo.completed_lesson_ids(session, user.id) if user else set()

    quiz = await quiz_repo.get_lesson_quiz(session, lesson.id)
    best_score = attempts = None
    if quiz is not None:
        best_score, attempts = await quiz_repo.attempt_stats_for_quiz(
            session, user.id, quiz.id
        )

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
        quiz_slug=quiz.slug if quiz else None,
        quiz_pass_score=quiz.pass_score if quiz else None,
        quiz_best_score=best_score,
        quiz_passed=(
            best_score is not None and quiz is not None and best_score >= quiz.pass_score
        ),
        quiz_attempts=attempts or 0,
        references=list(tr(lesson, "references", locale) or []),
        video_url=lesson.video_url,
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
    """Marks a lesson done.

    A lesson that has a quiz cannot be finished this way: passing the quiz is
    what completes it, and the API records that itself when the attempt is
    scored. Refusing here keeps the button from quietly bypassing the gate.
    """
    lesson = await content_repo.get_lesson_by_slug(session, slug)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )

    quiz = await quiz_repo.get_lesson_quiz(session, lesson.id)
    if quiz is not None:
        best, _ = await quiz_repo.attempt_stats_for_quiz(session, user.id, quiz.id)
        if best is None or best < quiz.pass_score:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"This lesson is completed by scoring at least "
                    f"{quiz.pass_score:.0f}% on its quiz."
                ),
            )

    return await _set_completion(session, user, slug, True)


@router.delete("/{slug}/complete", response_model=LessonCompleteResponse)
async def uncomplete_lesson(
    slug: str, session: SessionDep, user: CurrentUser
) -> LessonCompleteResponse:
    return await _set_completion(session, user, slug, False)
