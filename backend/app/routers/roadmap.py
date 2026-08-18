"""Roadmap: phases, weeks and the weekly schedule view."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentTrack, CurrentUser, Locale, SessionDep
from app.schemas.content import (
    LabSummary,
    PhaseDetail,
    PhaseSummary,
    WeeklySchedule,
)
from app.schemas.quiz import QuizSummary
from app.i18n import tr
from app.services import roadmap_service
from app.repositories import content_repo, quiz_repo

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


@router.get("/phases", response_model=list[PhaseSummary])
async def list_phases(
    session: SessionDep, track: CurrentTrack, user: CurrentUser, locale: Locale
) -> list[PhaseSummary]:
    return await roadmap_service.list_phases(session, track, user, locale)


@router.get("", response_model=list[PhaseDetail])
async def full_roadmap(
    session: SessionDep, track: CurrentTrack, user: CurrentUser, locale: Locale
) -> list[PhaseDetail]:
    """The whole phase -> week -> lesson tree, with progress when signed in."""
    return await roadmap_service.get_roadmap(session, track, user, locale)


@router.get("/phases/{slug}", response_model=PhaseDetail)
async def get_phase(
    slug: str, session: SessionDep, track: CurrentTrack, user: CurrentUser,
    locale: Locale,
) -> PhaseDetail:
    phase = await roadmap_service.get_phase(session, track, slug, user, locale)
    if phase is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found"
        )

    quizzes = await quiz_repo.list_quizzes(session, phase_slug=slug, track_id=track.id)
    best = await quiz_repo.best_scores(session, user.id) if user else {}
    counts = await quiz_repo.attempt_counts(session, user.id) if user else {}
    phase.quizzes = [
        QuizSummary(
            id=q.id,
            slug=q.slug,
            title=tr(q, "title", locale),
            description=tr(q, "description", locale),
            pass_score=q.pass_score,
            time_limit_minutes=q.time_limit_minutes,
            order_index=q.order_index,
            question_count=len(q.questions),
            phase_slug=slug,
            best_score=best.get(q.id),
            attempt_count=counts.get(q.id, 0),
            locked=phase.locked,
        )
        for q in quizzes
    ]

    labs = await content_repo.list_labs(session, track.id, phase_slug=slug)
    lab_status = await content_repo.lab_progress_map(session, user.id) if user else {}
    phase.labs = [
        LabSummary(
            id=lab.id,
            slug=lab.slug,
            title=tr(lab, "title", locale),
            description=tr(lab, "description", locale),
            difficulty=lab.difficulty,
            estimated_minutes=lab.estimated_minutes,
            order_index=lab.order_index,
            phase_slug=slug,
            status=lab_status.get(lab.id, "not_started"),
        )
        for lab in labs
    ]
    return phase


@router.get("/weeks/{number}/schedule", response_model=WeeklySchedule)
async def week_schedule(
    number: int, session: SessionDep, track: CurrentTrack, user: CurrentUser,
    locale: Locale,
) -> WeeklySchedule:
    schedule = await roadmap_service.weekly_schedule(
        session, track, number, user, locale
    )
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Week not found"
        )
    return schedule
