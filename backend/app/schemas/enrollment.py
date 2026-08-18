"""Enrollment payloads: starting a track, and the countdown that follows."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class EnrollmentRead(BaseModel):
    """Where one user stands in one track.

    Everything the timer needs arrives in one response, already computed - the
    browser does no date arithmetic of its own beyond ticking the seconds.
    """

    model_config = ConfigDict(from_attributes=True)

    track_slug: str
    status: str  # not_started | active | completed
    duration_weeks: int

    # Present only before Start: what the target WOULD be if pressed now, so the
    # Start screen can answer "how long is this going to take" honestly.
    projected_target_date: date | None = None

    started_at: datetime | None = None
    target_date: date | None = None
    auto_target_date: date | None = None
    target_source: str | None = None  # auto | manual

    days_total: int = 0
    days_elapsed: int = 0
    # Negative once the target has passed - the sign is what the UI counts up
    # from, so it is deliberately not clamped.
    days_remaining: int = 0
    is_overdue: bool = False

    expected_week: int = 0
    actual_week: int = 0
    behind_by_weeks: int = 0
    completed_at: datetime | None = None

    # The server's clock. A browser with a wrong clock would otherwise drift the
    # countdown by however far it is off; the client stores the offset once and
    # ticks against that.
    server_now: datetime


class EnrollmentUpdate(BaseModel):
    """`target_date: null` restores the date the roadmap suggests."""

    target_date: date | None = Field(
        default=None,
        description="Explicit target date, or null to fall back to the roadmap's own",
    )


class TrackSummaryStatus(BaseModel):
    """The compact status attached to each entry in GET /tracks.

    Enough for the switcher and the "My tracks" cards without a request per
    track.
    """

    status: str  # not_started | active | completed
    current_week: int | None = None
    duration_weeks: int = 0
    is_overdue: bool = False
    days_remaining: int | None = None
