"""What the bot does when someone types something.

Each handler is a thin shell: open a session, call a service, format a message.
The decisions - which lessons count as today's, how far along somebody is - live
in the service layer and are shared with the API and with the daily reminder, so
the bot cannot develop its own opinion about them.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.bot import messages
from app.db import SessionLocal
from app.models import User
from app.repositories import telegram_repo
from app.services import enrollment_service, telegram_service

log = logging.getLogger("app.bot")


def _display_name(user: User) -> str:
    return user.full_name or user.username or user.email


async def _reply(update: Update, text: str) -> None:
    if update.effective_message is None:
        return
    await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """`/start` with a token links the account; without one, it explains itself.

    Staying silent on a bare `/start` is the single most common way a bot looks
    broken - it is the first thing anybody types.
    """
    chat = update.effective_chat
    if chat is None:
        return

    token = context.args[0] if context.args else None

    async with SessionLocal() as session:
        if token is None:
            existing = await telegram_repo.get_by_chat_id(session, chat.id)
            if existing is not None:
                await _reply(update, messages.ALREADY_LINKED.format(name=_display_name(existing)))
            else:
                await _reply(update, messages.WELCOME_UNLINKED)
            return

        try:
            user = await telegram_service.redeem_link_token(
                session,
                token=token,
                chat_id=chat.id,
                username=update.effective_user.username if update.effective_user else None,
            )
        except telegram_service.LinkError as err:
            await _reply(update, messages.LINK_ERRORS.get(err.code, messages.ERROR))
            return

        await _reply(update, messages.LINKED.format(name=_display_name(user)))


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return

    async with SessionLocal() as session:
        user = await telegram_repo.get_by_chat_id(session, chat.id)
        if user is None:
            await _reply(update, messages.NOT_LINKED)
            return
        await telegram_service.unlink(session, user)
        await _reply(update, messages.UNLINKED)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, messages.HELP)


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return

    async with SessionLocal() as session:
        user = await telegram_repo.get_by_chat_id(session, chat.id)
        if user is None:
            await _reply(update, messages.NOT_LINKED)
            return

        plans = await telegram_service.todays_plan(session, user)
        if not plans:
            await _reply(update, messages.NOTHING_TODAY)
            return

        blocks: list[str] = []
        for plan in plans:
            if plan.is_lab_day:
                blocks.append(
                    messages.LAB_DAY.format(track=plan.track_title, week=plan.week_number)
                )
                continue
            if plan.is_review_day:
                blocks.append(
                    messages.REVIEW_DAY.format(track=plan.track_title, week=plan.week_number)
                )
                continue
            if not plan.lessons:
                continue
            listing = "\n".join(f"• {lesson.title}" for lesson in plan.lessons)
            blocks.append(
                messages.TODAY_HEADER.format(
                    track=plan.track_title,
                    week=plan.week_number,
                    count=len(plan.lessons),
                )
                + "\n"
                + listing
            )

        await _reply(update, "\n\n".join(blocks) if blocks else messages.NOTHING_TODAY)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return

    async with SessionLocal() as session:
        user = await telegram_repo.get_by_chat_id(session, chat.id)
        if user is None:
            await _reply(update, messages.NOT_LINKED)
            return

        plans = await telegram_service.todays_plan(session, user)
        if not plans:
            await _reply(update, messages.STATUS_NONE)
            return

        from app.models import Track
        from sqlalchemy import select

        blocks: list[str] = []
        for plan in plans:
            track = (
                await session.execute(select(Track).where(Track.slug == plan.track_slug))
            ).scalar_one_or_none()
            if track is None:
                continue

            # The same function the dashboard reads, so the two cannot disagree
            # about what week somebody is in.
            state = await enrollment_service.describe(session, user, track)
            percent = (
                round((state.days_elapsed / state.days_total) * 100)
                if state.days_total
                else 0
            )
            remaining = (
                messages.STATUS_OVERDUE.format(
                    days=abs(state.days_remaining), date=state.target_date
                )
                if state.is_overdue
                else messages.STATUS_REMAINING.format(
                    days=state.days_remaining, date=state.target_date
                )
            )
            line = messages.STATUS_LINE.format(
                track=track.title,
                week=state.expected_week,
                total=state.duration_weeks,
                percent=percent,
                remaining=remaining,
            )
            if state.behind_by_weeks:
                line += messages.STATUS_BEHIND.format(weeks=state.behind_by_weeks)
            blocks.append(line)

        await _reply(update, "\n\n".join(blocks) if blocks else messages.STATUS_NONE)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Never let an exception take the poller down.

    A bot that dies on one malformed update stops answering everybody, and long
    polling gives no external health signal that would catch it.
    """
    log.exception("Unhandled error in a Telegram handler", exc_info=context.error)
