"""User persistence."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole


async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(func.lower(User.email) == email.strip().lower())
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_by_oauth(
    session: AsyncSession, provider: str, subject: str
) -> User | None:
    stmt = select(User).where(
        User.oauth_provider == provider, User.oauth_subject == subject
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def create(
    session: AsyncSession,
    *,
    email: str,
    hashed_password: str | None = None,
    full_name: str | None = None,
    role: str = UserRole.STUDENT.value,
    oauth_provider: str | None = None,
    oauth_subject: str | None = None,
    avatar_url: str | None = None,
) -> User:
    user = User(
        email=email.strip().lower(),
        hashed_password=hashed_password,
        full_name=full_name,
        role=role,
        oauth_provider=oauth_provider,
        oauth_subject=oauth_subject,
        avatar_url=avatar_url,
    )
    session.add(user)
    await session.flush()
    return user


async def count_by_role(session: AsyncSession) -> dict[str, int]:
    stmt = select(User.role, func.count(User.id)).group_by(User.role)
    rows = (await session.execute(stmt)).all()
    return {role: count for role, count in rows}
