"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.i18n import normalize_locale, pick_locale
from app.models import User, UserRole
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


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
