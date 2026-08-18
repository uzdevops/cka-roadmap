"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import false as sa_false, or_, select, true as sa_true
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.i18n import normalize_locale, pick_locale
from app.models import Track, User, UserRole
from app.repositories import user_repo
from app.security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CredentialsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


async def _user_from_token(session: AsyncSession, token: str) -> User | None:
    try:
        payload = decode_token(token, expected_type="access")
    except jwt.PyJWTError:
        return None
    user = await user_repo.get_by_id(session, int(payload["sub"]))
    if user is None or not user.is_active:
        return None
    return user


async def get_current_user(
    session: SessionDep, credentials: CredentialsDep
) -> User:
    if credentials is None:
        raise _UNAUTHORIZED
    user = await _user_from_token(session, credentials.credentials)
    if user is None:
        raise _UNAUTHORIZED
    return user


async def get_optional_user(
    session: SessionDep, credentials: CredentialsDep
) -> User | None:
    """Public endpoints use this so progress can be layered in when signed in."""
    if credentials is None:
        return None
    return await _user_from_token(session, credentials.credentials)


async def require_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
AdminUser = Annotated[User, Depends(require_admin)]


async def get_locale(
    lang: Annotated[str | None, Query(description="Content language: en | uz")] = None,
    accept_language: Annotated[str | None, Header()] = None,
) -> str:
    """Explicit `?lang=` wins; otherwise negotiate from Accept-Language."""
    if lang:
        return normalize_locale(lang)
    return pick_locale(accept_language)


Locale = Annotated[str, Depends(get_locale)]


def _visible_to(user: User):
    """SQL half of `User.may_see_track` - kept next to it so the two cannot drift.

    An admin has no restriction; a student sees a track when either of its
    categories is granted, which is what makes a dual-nature track like CKA
    visible to both kinds of student.
    """
    if user.role == UserRole.ADMIN.value:
        return sa_true()
    clauses = []
    if user.access_topics:
        clauses.append(Track.is_topic.is_(True))
    if user.access_certificates:
        clauses.append(Track.is_certificate.is_(True))
    if not clauses:
        return sa_false()
    return or_(*clauses)


async def get_track(
    session: SessionDep,
    user: CurrentUser,
    track: Annotated[
        str | None, Query(description="Track slug, e.g. cka | docker | lfcs")
    ] = None,
) -> Track:
    """Which programme of study this request is about.

    Optional and defaulted on purpose. Making it required would break every
    route and every existing client in one commit, on a site that redeploys on
    every push; defaulted, the backend can ship scoped while the deployed
    frontend still calls the old URLs and keeps working.

    Explicit `?track=` wins, otherwise the lowest-ordered published track.

    It depends on `CurrentUser` so that authentication resolves first: without
    that, an anonymous request to a content route could be answered by this
    dependency before the auth check ran, turning a 401 into something else.
    """
    if track:
        found = (
            await session.execute(
                select(Track).where(Track.slug == track.strip().lower())
            )
        ).scalar_one_or_none()
        if found is None or not found.is_published:
            raise HTTPException(status_code=404, detail=f"Unknown track: {track}")
        if not user.may_see_track(
            is_topic=found.is_topic, is_certificate=found.is_certificate
        ):
            # 403, not 404: the track exists and the answer does not depend on
            # anything secret, so pretending otherwise only confuses the user.
            raise HTTPException(
                status_code=403,
                detail=f"Your account does not have access to {found.slug}",
            )
        return found

    default = (
        await session.execute(
            select(Track)
            .where(Track.is_published.is_(True), _visible_to(user))
            .order_by(Track.order_index, Track.id)
            .limit(1)
        )
    ).scalar_one_or_none()
    if default is None:
        # A database with no tracks at all is a fresh install, not an error.
        # This sentinel matches no phase, week or lesson, so every scoped query
        # returns nothing and the endpoints answer with empty lists rather than
        # failing. It is never persisted.
        return Track(id=-1, slug="", title="", is_topic=False, is_certificate=False)
    return default


CurrentTrack = Annotated[Track, Depends(get_track)]


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
