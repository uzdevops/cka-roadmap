"""The programmes of study this account may open.

This is what the track switcher reads. It returns only the tracks the signed-in
user is allowed to see, so the UI never offers a choice the API would then
refuse with a 403.
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.deps import CurrentUser, Locale, SessionDep, _visible_to
from app.i18n import tr
from app.models import Track
from app.schemas.content import TrackRead

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
        )
        for t in tracks
    ]
