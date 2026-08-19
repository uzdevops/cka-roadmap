"""Connecting a web account to a Telegram chat.

Nothing here touches the network. The bot's handlers are exercised against a
fake Update and a patched session factory, and the service layer - where every
decision actually lives - is called directly.

The security properties are the point of most of these: a link token is a
credential, and one that could be replayed, or redeemed by somebody else, or
pointed at a second account, would hand over an account rather than connect one.
"""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import TelegramLinkToken, User, UserRole
from app.security import hash_password
from app.services import telegram_service
from tests.conftest import auth_header, login

API = settings.api_v1_prefix
PASSWORD = "telegram-test-password"


@pytest.fixture(autouse=True)
def configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Most tests need the feature switched on; the ones about it being off say
    so explicitly."""
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    monkeypatch.setattr(settings, "telegram_bot_username", "cka_prep_test_bot")


async def _person(session: AsyncSession, username: str) -> User:
    user = User(
        email=f"{username}@example.com",
        username=username,
        hashed_password=hash_password(PASSWORD),
        full_name=username.title(),
        role=UserRole.STUDENT.value,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    return user


def _update(chat_id: int, username: str | None = "tg_user"):
    """The slice of a telegram Update the handlers actually read."""
    message = SimpleNamespace(reply_text=AsyncMock())
    return SimpleNamespace(
        effective_chat=SimpleNamespace(id=chat_id),
        effective_user=SimpleNamespace(username=username),
        effective_message=message,
    ), message


def _context(args: list[str] | None = None):
    return SimpleNamespace(args=args or [], error=None)


# --- the token ---------------------------------------------------------------


async def test_a_token_links_the_account_and_is_then_spent(
    session: AsyncSession
) -> None:
    user = await _person(session, "alice")
    offer = await telegram_service.issue_link_token(session, user)
    await session.commit()

    linked = await telegram_service.redeem_link_token(
        session, offer.token, chat_id=555, username="alice_tg"
    )
    assert linked.id == user.id
    assert linked.telegram_chat_id == 555
    assert linked.telegram_username == "alice_tg"
    assert linked.telegram_linked_at is not None

    # Spent. A link forwarded into a group chat must not claim the account.
    with pytest.raises(telegram_service.LinkError) as caught:
        await telegram_service.redeem_link_token(
            session, offer.token, chat_id=999, username="thief"
        )
    assert caught.value.code == "used"


async def test_an_expired_token_is_refused_with_a_reason(
    session: AsyncSession
) -> None:
    user = await _person(session, "bob")
    offer = await telegram_service.issue_link_token(session, user)
    await session.commit()

    row = (
        await session.execute(
            select(TelegramLinkToken).where(TelegramLinkToken.token == offer.token)
        )
    ).scalar_one()
    row.expires_at = telegram_service.utcnow() - timedelta(minutes=1)
    await session.commit()

    with pytest.raises(telegram_service.LinkError) as caught:
        await telegram_service.redeem_link_token(
            session, offer.token, chat_id=1, username=None
        )
    assert caught.value.code == "expired"


async def test_an_unknown_token_is_refused(session: AsyncSession) -> None:
    with pytest.raises(telegram_service.LinkError) as caught:
        await telegram_service.redeem_link_token(
            session, "not-a-real-token", chat_id=1, username=None
        )
    assert caught.value.code == "unknown"


async def test_issuing_a_new_token_invalidates_the_old_one(
    session: AsyncSession
) -> None:
    """Otherwise a link somebody generated and abandoned stays live for its full
    TTL alongside the one they are actually using."""
    user = await _person(session, "carol")
    first = await telegram_service.issue_link_token(session, user)
    await session.commit()
    second = await telegram_service.issue_link_token(session, user)
    await session.commit()

    with pytest.raises(telegram_service.LinkError) as caught:
        await telegram_service.redeem_link_token(
            session, first.token, chat_id=1, username=None
        )
    assert caught.value.code == "unknown"

    linked = await telegram_service.redeem_link_token(
        session, second.token, chat_id=2, username=None
    )
    assert linked.id == user.id


async def test_a_chat_cannot_be_pointed_at_a_second_account(
    session: AsyncSession
) -> None:
    """One Telegram account belongs to one web account - otherwise a reminder
    about somebody else's progress lands in the wrong chat."""
    first = await _person(session, "dave")
    second = await _person(session, "erin")

    offer_one = await telegram_service.issue_link_token(session, first)
    await session.commit()
    await telegram_service.redeem_link_token(
        session, offer_one.token, chat_id=777, username=None
    )

    offer_two = await telegram_service.issue_link_token(session, second)
    await session.commit()
    with pytest.raises(telegram_service.LinkError) as caught:
        await telegram_service.redeem_link_token(
            session, offer_two.token, chat_id=777, username=None
        )
    assert caught.value.code == "chat_taken"


async def test_a_token_only_ever_links_its_own_owner(session: AsyncSession) -> None:
    """The token names the account; nothing the caller sends can redirect it."""
    owner = await _person(session, "frank")
    other = await _person(session, "grace")

    offer = await telegram_service.issue_link_token(session, owner)
    await session.commit()

    linked = await telegram_service.redeem_link_token(
        session, offer.token, chat_id=42, username=None
    )
    assert linked.id == owner.id
    assert other.telegram_chat_id is None


# --- the endpoints -----------------------------------------------------------


async def test_the_link_endpoint_returns_a_deep_link(
    session: AsyncSession, client: AsyncClient
) -> None:
    await _person(session, "heidi")
    token = await login(client, "heidi", PASSWORD)

    response = await client.post(
        f"{API}/telegram/link-token", headers=auth_header(token)
    )
    assert response.status_code == 201, response.text
    body = response.json()

    assert body["url"].startswith("https://t.me/cka_prep_test_bot?start=")
    assert body["ttl_minutes"] == settings.link_token_ttl_minutes
    assert body["expires_at"]


async def test_the_link_endpoint_is_refused_when_no_bot_is_configured(
    session: AsyncSession, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    await _person(session, "ivan")
    token = await login(client, "ivan", PASSWORD)

    response = await client.post(
        f"{API}/telegram/link-token", headers=auth_header(token)
    )
    assert response.status_code == 503


async def test_auth_config_reports_the_bot_as_disabled_without_a_token(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """This is what makes the UI hide every mention of it."""
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    response = await client.get(f"{API}/auth/config")
    assert response.json()["telegram_enabled"] is False


async def test_auth_config_reports_it_as_enabled_when_configured(
    client: AsyncClient
) -> None:
    response = await client.get(f"{API}/auth/config")
    assert response.json()["telegram_enabled"] is True


async def test_status_and_disconnect_from_the_site(
    session: AsyncSession, client: AsyncClient
) -> None:
    user = await _person(session, "judy")
    offer = await telegram_service.issue_link_token(session, user)
    await session.commit()
    await telegram_service.redeem_link_token(
        session, offer.token, chat_id=321, username="judy_tg"
    )

    token = await login(client, "judy", PASSWORD)

    status = await client.get(f"{API}/telegram/status", headers=auth_header(token))
    assert status.json()["linked"] is True
    assert status.json()["username"] == "judy_tg"

    gone = await client.delete(f"{API}/telegram/link", headers=auth_header(token))
    assert gone.status_code == 200
    assert gone.json()["linked"] is False

    # Idempotent: asking again for the state you are already in is not an error.
    again = await client.delete(f"{API}/telegram/link", headers=auth_header(token))
    assert again.status_code == 200


# --- the bot handlers, with no network -------------------------------------


async def test_start_with_a_token_links_the_chat(session: AsyncSession) -> None:
    from app.bot import handlers, messages

    user = await _person(session, "karl")
    offer = await telegram_service.issue_link_token(session, user)
    await session.commit()

    update, message = _update(chat_id=1010, username="karl_tg")

    class _Factory:
        def __call__(self):
            return self

        async def __aenter__(self):
            return session

        async def __aexit__(self, *exc):
            return False

    with patch.object(handlers, "SessionLocal", _Factory()):
        await handlers.start(update, _context([offer.token]))

    message.reply_text.assert_awaited()
    said = message.reply_text.await_args.args[0]
    assert "Connected" in said

    await session.refresh(user)
    assert user.telegram_chat_id == 1010


async def test_start_without_a_token_explains_itself(session: AsyncSession) -> None:
    """A bot that says nothing to a bare /start looks broken, and /start is the
    first thing anybody types."""
    from app.bot import handlers

    update, message = _update(chat_id=2020)

    class _Factory:
        def __call__(self):
            return self

        async def __aenter__(self):
            return session

        async def __aexit__(self, *exc):
            return False

    with patch.object(handlers, "SessionLocal", _Factory()):
        await handlers.start(update, _context([]))

    said = message.reply_text.await_args.args[0]
    assert "Connect Telegram" in said


async def test_stop_unlinks_the_chat(session: AsyncSession) -> None:
    from app.bot import handlers

    user = await _person(session, "lena")
    offer = await telegram_service.issue_link_token(session, user)
    await session.commit()
    await telegram_service.redeem_link_token(
        session, offer.token, chat_id=3030, username=None
    )

    update, message = _update(chat_id=3030)

    class _Factory:
        def __call__(self):
            return self

        async def __aenter__(self):
            return session

        async def __aexit__(self, *exc):
            return False

    with patch.object(handlers, "SessionLocal", _Factory()):
        await handlers.stop(update, _context())

    assert "Disconnected" in message.reply_text.await_args.args[0]
    await session.refresh(user)
    assert user.telegram_chat_id is None


async def test_an_expired_link_is_explained_not_just_refused(
    session: AsyncSession
) -> None:
    from app.bot import handlers

    user = await _person(session, "mona")
    offer = await telegram_service.issue_link_token(session, user)
    await session.commit()
    row = (
        await session.execute(
            select(TelegramLinkToken).where(TelegramLinkToken.token == offer.token)
        )
    ).scalar_one()
    row.expires_at = telegram_service.utcnow() - timedelta(minutes=1)
    await session.commit()

    update, message = _update(chat_id=4040)

    class _Factory:
        def __call__(self):
            return self

        async def __aenter__(self):
            return session

        async def __aexit__(self, *exc):
            return False

    with patch.object(handlers, "SessionLocal", _Factory()):
        await handlers.start(update, _context([offer.token]))

    said = message.reply_text.await_args.args[0]
    assert "expired" in said.lower(), said
