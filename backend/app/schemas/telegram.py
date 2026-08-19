"""Telegram link payloads."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TelegramStatus(BaseModel):
    """Whether the bot exists at all, and whether this account is on it.

    `enabled` is separate from `linked` on purpose: with no token configured the
    UI hides the whole feature rather than offering a button that cannot work.
    """

    enabled: bool
    linked: bool
    username: str | None = None
    linked_at: datetime | None = None


class TelegramLinkOffer(BaseModel):
    """A t.me deep link, and how long it stays good for."""

    url: str
    expires_at: datetime
    ttl_minutes: int
