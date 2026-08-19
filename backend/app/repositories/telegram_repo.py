"""Link-token and Telegram-account persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TelegramLinkToken, User


async def add_token(session: AsyncSession, token: TelegramLinkToken) -> TelegramLinkToken:
    session.add(token)
    await session.flush()
    return token


async def get_token(session: AsyncSession, token: str) -> TelegramLinkToken | None:
    stmt = select(TelegramLinkToken).where(TelegramLinkToken.token == token)
    return (await session.execute(stmt)).scalar_one_or_none()


async def clear_tokens_for(session: AsyncSession, user_id: int) -> None:
    """Issuing a new link invalidates the previous ones.

    Otherwise a link somebody generated, abandoned and left in a chat history
    stays live for its full TTL alongside the one they are actually using.
    """
    await session.execute(
        delete(TelegramLinkToken).where(TelegramLinkToken.user_id == user_id)
    )


async def purge_expired(session: AsyncSession, now: datetime) -> int:
    """Housekeeping. Nothing depends on it - an expired token is refused on its
    own merits - but the table should not grow forever."""
    result = await session.execute(
        delete(TelegramLinkToken).where(TelegramLinkToken.expires_at < now)
    )
    return int(result.rowcount or 0)


async def get_by_chat_id(session: AsyncSession, chat_id: int) -> User | None:
    stmt = select(User).where(User.telegram_chat_id == chat_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def list_linked_users(session: AsyncSession) -> list[User]:
    """Everyone reachable on Telegram - the audience for PR 4's reminder."""
    stmt = select(User).where(
        User.telegram_chat_id.is_not(None), User.is_active.is_(True)
    )
    return list((await session.execute(stmt)).scalars().all())
