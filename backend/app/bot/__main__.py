"""`python -m app.bot` - the long-polling entry point.

Long polling rather than a webhook: a webhook needs a public URL and a valid
certificate, which would tie the bot to the deployment's DNS and TLS. Polling
works from anywhere, including a laptop.

The direct consequence is that this must run as EXACTLY ONE process. Two
pollers on one token fight over every update and Telegram rejects one of them,
so `replicas: 1` in the deployment files is a correctness constraint, not a
capacity choice.
"""

from __future__ import annotations

import logging
import sys

from app.config import settings

log = logging.getLogger("app.bot")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s %(name)s: %(message)s",
    )

    if not settings.telegram_enabled:
        # A clean exit, not a crash. The service is optional, and a container
        # that keeps restarting on a missing optional setting buries real
        # failures in noise - and on Swarm it would restart forever.
        log.info(
            "TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_USERNAME is not set - "
            "the bot is disabled and this process is exiting normally."
        )
        return 0

    # Imported here rather than at module scope so the check above can run - and
    # report a clear reason - even in an image where the library is absent.
    from telegram.ext import ApplicationBuilder, CommandHandler

    from app.bot import handlers

    app = ApplicationBuilder().token(settings.telegram_bot_token).build()

    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("stop", handlers.stop))
    app.add_handler(CommandHandler("help", handlers.help_command))
    app.add_handler(CommandHandler("today", handlers.today))
    app.add_handler(CommandHandler("status", handlers.status))
    app.add_error_handler(handlers.on_error)

    log.info("Bot starting as @%s (long polling)", settings.telegram_bot_username)
    # drop_pending_updates: after a restart, the backlog is stale. Answering a
    # day-old /today with today's plan is worse than not answering it.
    app.run_polling(drop_pending_updates=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
