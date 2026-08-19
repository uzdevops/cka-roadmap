"""Everything the bot says, in one place.

English only, by decision: the bot has no reliable way to know a person's
interface language before they are linked, and a half-translated bot is worse
than a consistently English one. The website stays bilingual.

Kept out of the handlers so the wording can be changed without touching the
flow, and so a reviewer can read what a user will actually see without reading
any code.
"""

from __future__ import annotations

WELCOME_UNLINKED = (
    "Hello. I send you a nudge at the end of the day if the lessons you planned "
    "are still unfinished.\n\n"
    "I do not know who you are yet. Open your profile on the site and press "
    "*Connect Telegram* - that gives you a button which brings you back here "
    "already linked."
)

LINKED = (
    "Connected. You are signed in as *{name}*.\n\n"
    "/today - what is on your plan today\n"
    "/status - how far along you are\n"
    "/stop - disconnect\n\n"
    "I will check in around 20:30 if the day's lessons are still open."
)

ALREADY_LINKED = "This chat is already connected to *{name}*. Nothing to do."

# One sentence per failure, each naming the actual cause and the way out. A
# single generic "invalid link" would leave somebody retrying the same dead link.
LINK_ERRORS = {
    "unknown": (
        "I do not recognise that link. Get a fresh one from your profile on the "
        "site."
    ),
    "used": (
        "That link has already been used. Links work once - get a new one from "
        "your profile."
    ),
    "expired": (
        "That link has expired. They are short-lived on purpose; get a new one "
        "from your profile."
    ),
    "chat_taken": (
        "This Telegram account is already connected to a different account on "
        "the site. Disconnect there first, then try again."
    ),
    "account_unavailable": (
        "That account is not available. If you think this is wrong, ask an "
        "administrator."
    ),
}

UNLINKED = (
    "Disconnected. I will not message you again.\n\n"
    "You can reconnect any time from your profile on the site."
)

NOT_LINKED = (
    "This chat is not connected to an account yet. Open your profile on the "
    "site and press *Connect Telegram*."
)

HELP = (
    "*What I do*\n"
    "I remind you about the day's lessons if they are still unfinished at "
    "20:30.\n\n"
    "*Commands*\n"
    "/today - today's lessons\n"
    "/status - progress and time left\n"
    "/stop - disconnect this chat\n"
    "/help - this message"
)

NOTHING_TODAY = "Nothing scheduled today. A rest day is part of the plan."

LAB_DAY = "*{track}* - week {week}\nToday is lab day. Open the labs on the site."

REVIEW_DAY = (
    "*{track}* - week {week}\nToday is review day. Go back over anything from "
    "this week that did not stick."
)

TODAY_HEADER = "*{track}* - week {week}, {count} lesson(s) today:"

STATUS_LINE = (
    "*{track}*\n"
    "Week {week} of {total} - {percent}% of the roadmap\n"
    "{remaining}"
)

STATUS_REMAINING = "{days} days until your target of {date}"
STATUS_OVERDUE = "{days} days past your target of {date}"
STATUS_BEHIND = "\nYou are {weeks} week(s) behind the plan."
STATUS_NONE = (
    "You have not started a track yet. Pick one on the site and press Start."
)

ERROR = "Something went wrong on my side. Try again in a moment."
