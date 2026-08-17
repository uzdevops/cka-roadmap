"""Hands-on labs (instructions-only in v1)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentUser, Locale, OptionalUser, SessionDep
from app.i18n import tr
from app.repositories import content_repo, progress_repo
from app.schemas.content import LabDetail, LabProgressUpdate, LabSummary

router = APIRouter(prefix="/labs", tags=["labs"])


@router.get("", response_model=list[LabSummary])
async def list_labs(
    session: SessionDep, user: OptionalUser, locale: Locale, phase: str | None = None
) -> list[LabSummary]:
    labs = await content_repo.list_labs(session, phase_slug=phase)
    statuses = await content_repo.lab_progress_map(session, user.id) if user else {}
    return [
        LabSummary(
            id=lab.id,
            slug=lab.slug,
            title=tr(lab, "title", locale),
            description=tr(lab, "description", locale),
            difficulty=lab.difficulty,
            estimated_minutes=lab.estimated_minutes,
            order_index=lab.order_index,
            phase_slug=lab.phase.slug if lab.phase else None,
            status=statuses.get(lab.id, "not_started"),
        )
        for lab in labs
    ]


@router.get("/{slug}", response_model=LabDetail)
async def get_lab(
    slug: str, session: SessionDep, user: OptionalUser, locale: Locale
) -> LabDetail:
    lab = await content_repo.get_lab_by_slug(session, slug)
    if lab is None or not lab.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab not found")

    statuses = await content_repo.lab_progress_map(session, user.id) if user else {}
    return LabDetail(
        id=lab.id,
        slug=lab.slug,
        title=tr(lab, "title", locale),
        description=tr(lab, "description", locale),
        difficulty=lab.difficulty,
        estimated_minutes=lab.estimated_minutes,
        order_index=lab.order_index,
        phase_slug=lab.phase.slug if lab.phase else None,
        status=statuses.get(lab.id, "not_started"),
        scenario=tr(lab, "scenario", locale),
        environment_setup=lab.environment_setup,
        cleanup=lab.cleanup,
        # Task prose is translated; the shell commands stay verbatim.
        tasks=_localized_tasks(lab, locale),
    )


def _localized_tasks(lab, locale: str) -> list[dict]:
    """Merges translated task prose over the English task list, task by task."""
    tasks = list(lab.tasks or [])
    translated = ((lab.translations or {}).get(locale) or {}).get("tasks")
    if not translated:
        return tasks
    merged = []
    for index, task in enumerate(tasks):
        override = translated[index] if index < len(translated) else {}
        merged.append({**task, **{k: v for k, v in (override or {}).items() if v}})
    return merged


@router.put("/{slug}/progress", response_model=LabSummary)
async def set_lab_progress(
    slug: str, payload: LabProgressUpdate, session: SessionDep, user: CurrentUser
) -> LabSummary:
    lab = await content_repo.get_lab_by_slug(session, slug)
    if lab is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab not found")

    await progress_repo.set_lab_status(session, user.id, lab.id, payload.status)
    if payload.status != "not_started":
        await progress_repo.record_activity(session, user.id)
    await session.commit()

    return LabSummary(
        id=lab.id,
        slug=lab.slug,
        title=lab.title,
        description=lab.description,
        difficulty=lab.difficulty,
        estimated_minutes=lab.estimated_minutes,
        order_index=lab.order_index,
        phase_slug=lab.phase.slug if lab.phase else None,
        status=payload.status,
    )
