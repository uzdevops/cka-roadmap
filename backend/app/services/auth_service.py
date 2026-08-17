"""Registration, login, refresh and profile updates."""

from __future__ import annotations

import jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole
from app.repositories import user_repo
from app.schemas.auth import TokenPair, UserRegister, UserUpdate
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect email or password",
    headers={"WWW-Authenticate": "Bearer"},
)


def issue_tokens(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
    )


async def register(session: AsyncSession, payload: UserRegister) -> User:
    existing = await user_repo.get_by_email(session, payload.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    user = await user_repo.create(
        session,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.STUDENT.value,
    )
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    user = await user_repo.get_by_email(session, email)
    if user is None or not verify_password(password, user.hashed_password):
        raise INVALID_CREDENTIALS
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
        )
    return user


async def refresh_tokens(session: AsyncSession, refresh_token: str) -> TokenPair:
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from exc

    user = await user_repo.get_by_id(session, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer active"
        )
    return issue_tokens(user)


async def update_profile(
    session: AsyncSession, user: User, payload: UserUpdate
) -> User:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(user, field, value)
    await session.commit()
    await session.refresh(user)
    return user


async def change_password(
    session: AsyncSession, user: User, current: str, new: str
) -> None:
    if user.hashed_password and not verify_password(current, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is wrong"
        )
    user.hashed_password = hash_password(new)
    await session.commit()


async def upsert_oauth_user(
    session: AsyncSession,
    *,
    provider: str,
    subject: str,
    email: str,
    full_name: str | None,
    avatar_url: str | None,
) -> User:
    """Link by provider subject first, then fall back to matching email."""
    user = await user_repo.get_by_oauth(session, provider, subject)
    if user is None:
        user = await user_repo.get_by_email(session, email)
    if user is None:
        user = await user_repo.create(
            session,
            email=email,
            full_name=full_name,
            oauth_provider=provider,
            oauth_subject=subject,
            avatar_url=avatar_url,
        )
    else:
        user.oauth_provider = provider
        user.oauth_subject = subject
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        if full_name and not user.full_name:
            user.full_name = full_name
    await session.commit()
    await session.refresh(user)
    return user
