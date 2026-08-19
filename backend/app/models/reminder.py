"""What was sent, to whom, and what they said.

This table is the reason a restarted bot does not send the same reminder twice:
the uniqueness lives in the database, where a process that has just lost its
memory cannot forget it.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReminderKind(str):
    DAILY_TASK = "daily_task"


class ReminderAnswer(str):
    YES = "yes"
    NO = "no"


class ReminderLog(Base):
    __tablename__ = "reminder_log"
    __table_args__ = (
        # One reminder per person per day per kind. This is the idempotency
        # guarantee, not a convenience index.
        UniqueConstraint(
            "user_id", "reminder_date", "kind", name="uq_reminder_user_date_kind"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    reminder_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    kind: Mapped[str] = mapped_column(
        String(20), default=ReminderKind.DAILY_TASK, nullable=False
    )

    # What the message listed. Stored so a button pressed tomorrow still knows
    # what it was about, rather than re-deriving "today" from a date that has
    # moved on.
    lesson_ids: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)

    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    answered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    answer: Mapped[str | None] = mapped_column(String(4), nullable=True)
    telegram_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
