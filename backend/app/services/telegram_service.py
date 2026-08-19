"""Connecting a web account to a Telegram chat, and what to say to it.

The link is made by deep link: the site hands out a one-time token, the button
opens Telegram with `/start <token>` already typed, and the bot redeems it. The
alternative - asking somebody to copy a code between two apps - fails often
enough that people give up on it.

Everything here is deliberately transport-free: nothing in this module talks to
Telegram. The bot calls these functions and does the talking, which is what lets
the whole flow be tested without a network.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Lesson, TelegramLinkToken, Track, TrackEnrollment, User, Week
from app.repositories import telegram_repo
from app.services import enrollment_service


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LinkError(Exception):
    """Why a token was refused, in a form the bot can turn into a sentence."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class LinkOffer:
    """What the site shows: a button, and how long it stays good for."""

    url: str
    token: str
    expires_at: datetime


async def issue_link_token(session: AsyncSession, user: User) -> LinkOffer:
    """A fresh single-use token, replacing any the user already had.

    `token_urlsafe(24)` is 32 characters of URL-safe base64 - comfortably past
    guessing, and short enough to survive being pasted into Telegram's start
    parameter, which is capped at 64.
    """
    await telegram_repo.clear_tokens_for(session, user.id)

    token = secrets.token_urlsafe(24)
    expires_at = utcnow() + timedelta(minutes=settings.link_token_ttl_minutes)

    await telegram_repo.add_token(
        session,
        TelegramLinkToken(
            token=token,
            user_id=user.id,
            expires_at=expires_at,
            created_at=utcnow(),
        ),
    )

    return LinkOffer(
        url=f"https://t.me/{settings.telegram_bot_username}?start={token}",
        token=token,
        expires_at=expires_at,
    )


async def redeem_link_token(
    session: AsyncSession, token: str, chat_id: int, username: str | None
) -> User:
    """Claim an account for a chat. Raises LinkError with a specific code.

    The checks are ordered from cheapest to most specific so the reason a person
    is told is the real one - "expired" rather than a generic failure.
    """
    row = await telegram_repo.get_token(session, token)
    if row is None:
        raise LinkError("unknown")
    if row.used_at is not None:
        raise LinkError("used")
    if row.expires_at < utcnow():
        raise LinkError("expired")

    # This chat may already belong to somebody else. The column is unique, so
    # the database would refuse anyway - catching it here means the person gets
    # an explanation instead of a failed command.
    existing = await telegram_repo.get_by_chat_id(session, chat_id)
    if existing is not None and existing.id != row.user_id:
        raise LinkError("chat_taken")

    user = await session.get(User, row.user_id)
    if user is None or not user.is_active:
        raise LinkError("account_unavailable")

    user.telegram_chat_id = chat_id
    user.telegram_username = username
    user.telegram_linked_at = utcnow()
    row.used_at = utcnow()

    await session.commit()
    return user


async def unlink(session: AsyncSession, user: User) -> None:
    """Disconnect, from either side.

    Also used when Telegram reports the bot as blocked: a chat that cannot be
    written to is not a link, and retrying forever would be the alternative.
    """
    user.telegram_chat_id = None
    user.telegram_username = None
    user.telegram_linked_at = None
    await telegram_repo.clear_tokens_for(session, user.id)
    await session.commit()


# --- what to say ------------------------------------------------------------


@dataclass(frozen=True)
class TodayPlan:
    """The lessons a person is meant to do today, in one track."""

    track_slug: str
    track_title: str
    week_number: int
    day_of_week: int
    lessons: list[Lesson]
    is_lab_day: bool
    is_review_day: bool


async def todays_plan(
    session: AsyncSession, user: User, on: datetime | None = None
) -> list[TodayPlan]:
    """Today's work across every track this person has started.

    Shared with the daily reminder, deliberately: the message sent at 20:30 and
    the answer to `/today` must not be able to disagree about what was due.

    `day_of_week` is 1-5 for lesson days, 6 for the lab day and 7 for review -
    the same convention the roadmap uses.
    """
    now = on or utcnow()
    weekday = now.isoweekday()

    enrollments = (
        await session.execute(
            select(TrackEnrollment).where(
                TrackEnrollment.user_id == user.id,
                TrackEnrollment.status == "active",
            )
        )
    ).scalars().all()

    plans: list[TodayPlan] = []
    for enrollment in enrollments:
        track = await session.get(Track, enrollment.track_id)
        if track is None:
            continue

        week_number = enrollment_service.expected_week(enrollment.started_at, on=now.date())
        total = await enrollment_service.duration_weeks(session, track)
        if total and week_number > total:
            # Past the end of the roadmap: there is no "today" left to do.
            continue

        lessons = (
            await session.execute(
                select(Lesson)
                .join(Week, Lesson.week_id == Week.id)
                .where(
                    Week.track_id == track.id,
                    Week.number == week_number,
                    Lesson.is_published.is_(True),
                    Lesson.day_of_week == weekday,
                )
                .order_by(Lesson.order_index, Lesson.id)
            )
        ).scalars().all()

        plans.append(
            TodayPlan(
                track_slug=track.slug,
                track_title=track.title,
                week_number=week_number,
                day_of_week=weekday,
                lessons=list(lessons),
                is_lab_day=weekday == 6,
                is_review_day=weekday == 7,
            )
        )
    return plans
