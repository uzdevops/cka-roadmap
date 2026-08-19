"""Sending the 20:30 nudge, and handling the answer.

The interesting part is what "Yes" is allowed to do. A button in a chat must not
be able to finish a lesson that the website would refuse to finish, so it goes
through `lesson_service` like the web button does - and when a quiz is
outstanding it records the lesson as READ and says so, rather than quietly doing
less than the person expected.

Nothing here decides what is due; `reminder_service` does, and the bot's
`/today` command reads the same selection.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import Forbidden, RetryAfter, TimedOut
from telegram.ext import ContextTypes

from app.bot import messages
from app.config import settings
from app.db import SessionLocal
from app.models import Lesson, ReminderAnswer, ReminderLog, Track
from app.services import lesson_service, reminder_service, telegram_service

log = logging.getLogger("app.bot.reminders")

WEEKDAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]

# A courtesy pause between sends. Telegram's documented ceiling is around 30
# messages a second; this stays far below it and keeps one slow send from
# stacking up behind the next.
SEND_GAP_SECONDS = 0.1


def _keyboard(reminder_id: int, lessons: list[Lesson]) -> InlineKeyboardMarkup:
    """Buttons that fit.

    `callback_data` is capped at 64 bytes by Telegram, so the payload carries
    the reminder's id and nothing else - a list of lesson ids would overflow it
    for anybody with more than a handful, and would go stale besides. The rows
    are what the message is about; the data is only a pointer to the log entry.
    """
    rows: list[list[InlineKeyboardButton]] = []
    if len(lessons) > 1:
        # One button per lesson would exceed nothing, but "did you study" is a
        # single question - so the per-lesson buttons answer it per lesson and
        # "All done" answers it for the day.
        rows.extend(
            [InlineKeyboardButton(f"✅ {lesson.title[:40]}", callback_data=f"r:{reminder_id}:l{lesson.id}")]
            for lesson in lessons
        )
        rows.append([InlineKeyboardButton(messages.BTN_ALL_DONE, callback_data=f"r:{reminder_id}:y")])
        rows.append([InlineKeyboardButton(messages.BTN_NO, callback_data=f"r:{reminder_id}:n")])
    else:
        rows.append(
            [
                InlineKeyboardButton(messages.BTN_YES, callback_data=f"r:{reminder_id}:y"),
                InlineKeyboardButton(messages.BTN_NO, callback_data=f"r:{reminder_id}:n"),
            ]
        )
    return InlineKeyboardMarkup(rows)


def _body(track_title: str, week: int, when: datetime, lessons: list[Lesson]) -> str:
    header = messages.REMINDER_HEADER.format(
        track=track_title, week=week, weekday=WEEKDAYS[when.weekday()]
    )
    listing = "\n".join(
        f"• {lesson.title} ({lesson.estimated_minutes} min)" for lesson in lessons
    )
    return f"{header}\n{listing}\n\n{messages.REMINDER_QUESTION}"


async def send_daily(context: ContextTypes.DEFAULT_TYPE) -> None:
    """The scheduled job.

    Every user is sent inside its own try/except: one blocked chat, or one
    account with odd data, must not stop the other ninety-nine from being
    reminded.
    """
    from zoneinfo import ZoneInfo

    zone = ZoneInfo(settings.reminder_tz)
    now = datetime.now(zone)

    if not reminder_service.is_lesson_day(now.date()):
        log.info("%s is not a lesson day - no reminders", now.date())
        return

    async with SessionLocal() as session:
        people = await reminder_service.audience(session)

    log.info("Daily reminder: %d candidate(s)", len(people))
    sent = 0

    for person in people:
        try:
            async with SessionLocal() as session:
                user = await session.merge(person, load=True)
                due = await reminder_service.due_today(session, user, when=now.date())
                if not due:
                    # Everything already done, or nothing scheduled. Silence is
                    # the correct message.
                    continue

                # One track per day: the first one they are behind on. Several
                # messages at once reads as spam and gets the bot muted.
                target = due[0]
                reminder = await reminder_service.claim_reminder(
                    session, user, target.track, target.lessons, now.date()
                )
                if reminder is None:
                    # Somebody - probably this process before it restarted -
                    # already sent today's.
                    continue

                text = _body(target.track.title, target.week_number, now, target.lessons)
                markup = _keyboard(reminder.id, target.lessons)
                chat_id = user.telegram_chat_id
                reminder_id = reminder.id

            message = await _send_with_retry(context, chat_id, text, markup)
            if message is not None:
                async with SessionLocal() as session:
                    row = await session.get(ReminderLog, reminder_id)
                    if row is not None:
                        row.telegram_message_id = message.message_id
                        await session.commit()
                sent += 1

            await asyncio.sleep(SEND_GAP_SECONDS)

        except Forbidden:
            # Blocked. Unlink rather than retry every evening forever - a chat
            # that refuses messages is not a link.
            log.info("Chat %s blocked the bot - unlinking", person.telegram_chat_id)
            async with SessionLocal() as session:
                user = await session.merge(person, load=True)
                await telegram_service.unlink(session, user)
        except Exception:
            log.exception("Reminder failed for user %s", person.id)

    log.info("Daily reminder: %d sent", sent)


async def _send_with_retry(context, chat_id: int, text: str, markup, attempts: int = 3):
    """Telegram rate-limits and times out; neither is a reason to lose a send."""
    for attempt in range(attempts):
        try:
            return await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=markup,
                parse_mode=ParseMode.MARKDOWN,
            )
        except RetryAfter as err:
            # The server has told us exactly how long to wait. Obey it.
            await asyncio.sleep(float(err.retry_after) + 0.5)
        except TimedOut:
            await asyncio.sleep(2 * (attempt + 1))
    log.warning("Giving up on chat %s after %d attempts", chat_id, attempts)
    return None


async def on_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """A button press on a reminder."""
    query = update.callback_query
    if query is None or not query.data:
        return
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 3 or parts[0] != "r":
        return
    try:
        reminder_id = int(parts[1])
    except ValueError:
        return
    choice = parts[2]

    async with SessionLocal() as session:
        reminder = await session.get(ReminderLog, reminder_id)
        if reminder is None:
            # Yesterday's message, or one whose row has since gone. Polite, not
            # an error - the person did nothing wrong.
            await _finish(query, messages.REMINDER_EXPIRED)
            return

        from app.models import User

        user = await session.get(User, reminder.user_id)
        track = await session.get(Track, reminder.track_id)
        if user is None or track is None:
            await _finish(query, messages.REMINDER_EXPIRED)
            return

        if choice == "n":
            await reminder_service.record_answer(session, reminder, ReminderAnswer.NO)
            late = await reminder_service.lateness(session, user, track)
            text = (
                messages.ANSWERED_NO.format(
                    days=late.days_behind,
                    actual=late.actual_week,
                    expected=late.expected_week,
                )
                if late.days_behind > 0
                else messages.ANSWERED_NO_ON_TRACK.format(
                    actual=late.actual_week, expected=late.expected_week
                )
            )
            await _finish(query, text)
            return

        # "Yes", for one lesson or for all of them.
        lesson_ids = (
            [int(choice[1:])] if choice.startswith("l") else list(reminder.lesson_ids or [])
        )

        pending: list[str] = []
        for lesson_id in lesson_ids:
            lesson = await session.get(Lesson, lesson_id)
            if lesson is None:
                continue
            result = await lesson_service.complete_or_mark_read(
                session, user, lesson, source="telegram"
            )
            if result.read_only and result.quiz_slug:
                pending.append(reminder_service.lesson_url(track.slug, result.quiz_slug))

        await reminder_service.record_answer(session, reminder, ReminderAnswer.YES)

        await _finish(
            query,
            messages.ANSWERED_READ_PENDING.format(url="\n".join(pending))
            if pending
            else messages.ANSWERED_YES,
        )


async def _finish(query, text: str) -> None:
    """Replace the buttons with the outcome.

    Editing rather than replying keeps the chat readable, and removing the
    keyboard stops the same answer being pressed twice.
    """
    try:
        await query.edit_message_text(text=text, reply_markup=None)
    except Exception:
        # The message may be too old to edit, or unchanged. Saying it once in a
        # reply is better than failing the callback.
        log.debug("Could not edit the reminder message", exc_info=True)
        if query.message is not None:
            await query.message.reply_text(text)
