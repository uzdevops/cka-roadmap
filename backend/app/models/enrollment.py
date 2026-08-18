"""A user's commitment to one track.

Every track starts separately. Until somebody presses Start on a track there is
no enrollment row for it, no dates, and - with ENFORCE_TRACK_START on - no
content either. That is the whole point: a twenty-week roadmap means nothing
without a day one to count from.

This is also where the target date lives now. It used to be a single
`users.target_exam_date`, which could only ever describe one exam; a person
studying CKA and LFCS at once needs two.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.content import Track
    from app.models.user import User


class EnrollmentStatus(str):
    """Values for `TrackEnrollment.status`. No pause state - a paused track is
    indistinguishable from one somebody simply has not opened this week, and it
    would need its own arithmetic to keep the countdown honest."""

    ACTIVE = "active"
    COMPLETED = "completed"


class TargetSource(str):
    """Where `target_date` came from.

    Kept explicit rather than inferred by comparing the two dates: they are equal
    the moment somebody manually picks the date the roadmap already suggested,
    and that person still meant to choose it.
    """

    AUTO = "auto"
    MANUAL = "manual"


class TrackEnrollment(Base, TimestampMixin):
    __tablename__ = "track_enrollments"
    __table_args__ = (
        # One start per person per track. Restarting moves the existing row
        # rather than adding a second, so the history stays unambiguous.
        UniqueConstraint("user_id", "track_id", name="uq_enrollment_user_track"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), index=True, nullable=False
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # What the roadmap implies, kept alongside whatever the user chose, so
    # clearing a manual date can restore the suggestion without recomputing it
    # from a `started_at` that may since have moved.
    auto_target_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_source: Mapped[str] = mapped_column(
        String(10), default=TargetSource.AUTO, nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20), default=EnrollmentStatus.ACTIVE, nullable=False, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="enrollments")
    track: Mapped["Track"] = relationship()
