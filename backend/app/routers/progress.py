"""Progress dashboard endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.deps import CurrentUser, Locale, SessionDep
from app.repositories import content_repo, progress_repo
from app.schemas.progress import DashboardResponse, StreakInfo
from app.services import progress_service

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    session: SessionDep, user: CurrentUser, locale: Locale
) -> DashboardResponse:
    return await progress_service.build_dashboard(session, user, locale)


@router.get("/streak", response_model=StreakInfo)
async def streak(session: SessionDep, user: CurrentUser) -> StreakInfo:
    days = await progress_repo.activity_days(session, user.id)
    return progress_service.compute_streaks(days)


@router.get("/overview")
async def overview(session: SessionDep, user: CurrentUser) -> dict:
    """Compact counters for the navbar / header widgets."""
    total = await content_repo.count_lessons(session)
    done = await progress_repo.count_completed_lessons(session, user.id)
    days = await progress_repo.activity_days(session, user.id)
    streak_info = progress_service.compute_streaks(days)
    return {
        "total_lessons": total,
        "completed_lessons": done,
        "percent": round((done / total) * 100, 1) if total else 0.0,
        "current_streak": streak_info.current_streak,
    }
