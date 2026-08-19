"""the daily reminder, and what it was answered with

`reminder_log` is what makes the reminder idempotent. The bot restarting at
20:31 must not send the day's message a second time, and an in-memory flag would
not survive that restart - which is exactly the case it has to cover. The
UNIQUE (user_id, reminder_date, kind) constraint is the guarantee: a duplicate
send is refused by the database rather than avoided by remembering.

`lesson_progress` gains `read_at` / `read_source` because answering "Yes" in
Telegram cannot mean the same thing as finishing a lesson. A lesson with a quiz
is completed by passing that quiz, and a button in a chat must not be able to
step around the gate - so it records that the lesson was READ and leaves
completion to the quiz.

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-19 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reminder_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("reminder_date", sa.Date(), nullable=False),
        sa.Column(
            "kind", sa.String(length=20), nullable=False, server_default="daily_task"
        ),
        # The lessons the message listed. Kept so a callback answered tomorrow
        # still knows what it was about, without re-deriving "today" from a date
        # that has since moved on.
        sa.Column(
            "lesson_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("answer", sa.String(length=4), nullable=True),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], ondelete="CASCADE"),
        # The idempotency guarantee. One reminder per person per day per kind,
        # enforced where a restart cannot forget it.
        sa.UniqueConstraint(
            "user_id", "reminder_date", "kind", name="uq_reminder_user_date_kind"
        ),
    )
    op.create_index("ix_reminder_log_user_id", "reminder_log", ["user_id"])
    op.create_index("ix_reminder_log_track_id", "reminder_log", ["track_id"])
    op.create_index("ix_reminder_log_date", "reminder_log", ["reminder_date"])

    op.add_column(
        "lesson_progress",
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "lesson_progress", sa.Column("read_source", sa.String(length=16), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("lesson_progress", "read_source")
    op.drop_column("lesson_progress", "read_at")

    op.drop_index("ix_reminder_log_date", table_name="reminder_log")
    op.drop_index("ix_reminder_log_track_id", table_name="reminder_log")
    op.drop_index("ix_reminder_log_user_id", table_name="reminder_log")
    op.drop_table("reminder_log")
