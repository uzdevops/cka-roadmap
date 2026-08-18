"""The programmes of study this account may open.

This is what the track switcher reads. It returns only the tracks the signed-in
user is allowed to see, so the UI never offers a choice the API would then
refuse with a 403.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentUser, Locale, SessionDep, _visible_to, resolve_track
from app.i18n import tr
from app.models import EnrollmentStatus, Track
from app.repositories import enrollment_repo, progress_repo
from app.schemas.content import TrackRead
from app.schemas.enrollment import (
    EnrollmentRead,
    EnrollmentUpdate,
    TrackSummaryStatus,
)
from app.services import enrollment_service

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.get("", response_model=list[TrackRead])
async def list_tracks(
    session: SessionDep, user: CurrentUser, locale: Locale
) -> list[TrackRead]:
    stmt = (
        select(Track)
        .where(Track.is_published.is_(True), _visible_to(user))
        .order_by(Track.order_index, Track.id)
    )
    tracks = (await session.execute(stmt)).scalars().all()

    # One query for every enrollment, rather than one per track.
    enrollments = await enrollment_repo.map_for_user(session, user.id)
    durations = {
        t.id: await enrollment_service.duration_weeks(session, t) for t in tracks
    }

    return [
        TrackRead(
            slug=t.slug,
            title=tr(t, "title", locale),
            short_title=t.short_title or t.title,
            summary=tr(t, "summary", locale),
            provider=t.provider,
            is_topic=t.is_topic,
            is_certificate=t.is_certificate,
            exam_code=t.exam_code,
            exam_minutes=t.exam_minutes,
            mark=t.mark,
            accent=t.accent,
            references=list(tr(t, "references", locale) or []),
            enrollment=_summary_status(enrollments.get(t.id), durations.get(t.id, 0)),
        )
        for t in tracks
    ]


def _summary_status(enrollment, weeks: int) -> TrackSummaryStatus:
    """The compact form used by the switcher - no dates, just where they are."""
    if enrollment is None:
        return TrackSummaryStatus(status="not_started", duration_weeks=weeks)

    clock = enrollment_service.countdown(
        enrollment.started_at, enrollment.target_date
    )
    week = enrollment_service.expected_week(enrollment.started_at)
    return TrackSummaryStatus(
        status=enrollment.status,
        current_week=min(week, weeks) if weeks else week,
        duration_weeks=weeks,
        is_overdue=clock.is_overdue and enrollment.status == EnrollmentStatus.ACTIVE,
        days_remaining=clock.days_remaining,
    )


def _read(track_slug: str, state: enrollment_service.EnrollmentState) -> EnrollmentRead:
    return EnrollmentRead(
        track_slug=track_slug,
        status=state.status,
        duration_weeks=state.duration_weeks,
        projected_target_date=state.projected_target_date,
        started_at=state.started_at,
        target_date=state.target_date,
        auto_target_date=state.auto_target_date,
        target_source=state.target_source,
        days_total=state.days_total,
        days_elapsed=state.days_elapsed,
        days_remaining=state.days_remaining,
        is_overdue=state.is_overdue,
        expected_week=state.expected_week,
        actual_week=state.actual_week,
        behind_by_weeks=state.behind_by_weeks,
        completed_at=state.completed_at,
        server_now=enrollment_service.utcnow(),
    )


@router.get("/{slug}/enrollment", response_model=EnrollmentRead)
async def get_enrollment(
    slug: str, session: SessionDep, user: CurrentUser
) -> EnrollmentRead:
    """Deliberately reachable before Start - that screen needs these numbers."""
    track = await resolve_track(session, user, slug)
    state = await enrollment_service.describe(session, user, track)
    return _read(track.slug, state)


@router.post("/{slug}/start", response_model=EnrollmentRead, status_code=201)
async def start_track(
    slug: str, session: SessionDep, user: CurrentUser
) -> EnrollmentRead:
    """Idempotent: starting an already-started track returns it unchanged.

    Not a 409. A double-tapped button, a retried request and a second tab are
    all ordinary, and none of them should be able to move somebody's day one -
    but none of them is an error worth showing either.
    """
    track = await resolve_track(session, user, slug)
    enrollment, created = await enrollment_service.start(session, user, track)
    if created:
        # The day you commit to a track counts as a study day.
        await progress_repo.record_activity(session, user.id)
    await session.commit()

    state = await enrollment_service.describe(session, user, track)
    return _read(track.slug, state)


@router.patch("/{slug}/enrollment", response_model=EnrollmentRead)
async def update_enrollment(
    slug: str,
    payload: EnrollmentUpdate,
    session: SessionDep,
    user: CurrentUser,
) -> EnrollmentRead:
    track = await resolve_track(session, user, slug)
    enrollment = await enrollment_repo.get(session, user.id, track.id)
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This track has not been started",
        )
    enrollment_service.set_target_date(enrollment, payload.target_date)
    await session.commit()

    state = await enrollment_service.describe(session, user, track)
    return _read(track.slug, state)


@router.post("/{slug}/restart", response_model=EnrollmentRead)
async def restart_track(
    slug: str, session: SessionDep, user: CurrentUser
) -> EnrollmentRead:
    """Moves day one to today. Progress is kept - see enrollment_service."""
    track = await resolve_track(session, user, slug)
    enrollment = await enrollment_repo.get(session, user.id, track.id)
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This track has not been started",
        )
    await enrollment_service.restart(session, enrollment, track)
    await session.commit()

    state = await enrollment_service.describe(session, user, track)
    return _read(track.slug, state)
