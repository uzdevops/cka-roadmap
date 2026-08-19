"""Start dates, target dates and how far behind somebody is.

Every one of these numbers is computed here and nowhere else. The dashboard
card, the track list, the countdown component and - from PR 4 - the Telegram
reminder all read the same functions, so "week 6 of 20" cannot mean one thing on
the dashboard and another in a message sent that evening.

The pure arithmetic is deliberately separated from the database access: dates
are the part that is easy to get subtly wrong, and a function that only takes
dates can be tested without a session.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import EnrollmentStatus, TargetSource, Track, TrackEnrollment, User
from app.repositories import content_repo, enrollment_repo, quiz_repo


def utcnow() -> datetime:
    """Timezone-aware. A naive datetime subtracted from an aware one raises, and
    the columns here are timestamptz."""
    return datetime.now(timezone.utc)


def today() -> date:
    return utcnow().date()


# --- pure arithmetic ---------------------------------------------------------


def auto_target_date(started_at: datetime | date, weeks: int) -> date:
    """Day one plus the roadmap's length.

    Anchored on the start DATE, not the timestamp: somebody who presses Start at
    23:50 should not get a target a day earlier than somebody who pressed it at
    00:10 the same night.
    """
    start = started_at.date() if isinstance(started_at, datetime) else started_at
    return start + timedelta(weeks=max(weeks, 0))


def expected_week(started_at: datetime | date, on: date | None = None) -> int:
    """Which week the calendar says they should be in, counting from 1.

    Day one is week 1, not week 0 - a person who starts today is in their first
    week, and showing "week 0 of 20" reads as an error.
    """
    start = started_at.date() if isinstance(started_at, datetime) else started_at
    days = ((on or today()) - start).days
    if days < 0:
        return 1
    return days // 7 + 1


@dataclass(frozen=True)
class Countdown:
    """Everything the timer needs, derived once."""

    days_total: int
    days_elapsed: int
    days_remaining: int
    is_overdue: bool


def countdown(
    started_at: datetime | date, target: date, on: date | None = None
) -> Countdown:
    start = started_at.date() if isinstance(started_at, datetime) else started_at
    now = on or today()
    total = (target - start).days
    elapsed = (now - start).days
    remaining = (target - now).days
    return Countdown(
        days_total=max(total, 0),
        # Clamped at both ends: negative means the clock is wrong, and past the
        # target the bar is full rather than over-full.
        days_elapsed=max(0, min(elapsed, max(total, 0))),
        # NOT clamped - the sign is the overdue signal the UI counts up from.
        days_remaining=remaining,
        is_overdue=remaining < 0,
    )


def behind_by_weeks(expected: int, actual: int) -> int:
    """Never negative. Being ahead of the plan is not "minus two weeks behind";
    it is simply not behind, and the UI has a separate state for it."""
    return max(0, expected - actual)


# --- database-backed ---------------------------------------------------------


async def duration_weeks(session: AsyncSession, track: Track) -> int:
    """How long this track is meant to take.

    Three sources, in order of how much they actually know:
      1. the furthest `week_end` its phases declare - the roadmap's own answer;
      2. the number of weeks that exist, for a track with structure but no
         phase ranges;
      3. TRACK_DEFAULT_WEEKS, so an empty track still has a target date to
         show on its Start screen.
    """
    weeks = await enrollment_repo.max_week_end(session, track.id)
    if weeks > 0:
        return weeks
    weeks = await enrollment_repo.count_weeks(session, track.id)
    if weeks > 0:
        return weeks
    return settings.track_default_weeks


async def start(
    session: AsyncSession, user: User, track: Track
) -> tuple[TrackEnrollment, bool]:
    """Press Start. Returns (enrollment, created).

    Idempotent by contract: starting a track that is already started returns the
    existing row rather than an error. A double-tapped button, a retried request
    and a second browser tab must not be able to move somebody's day one.
    """
    existing = await enrollment_repo.get(session, user.id, track.id)
    if existing is not None:
        return existing, False

    now = utcnow()
    weeks = await duration_weeks(session, track)
    target = auto_target_date(now, weeks)

    enrollment = TrackEnrollment(
        user_id=user.id,
        track_id=track.id,
        started_at=now,
        auto_target_date=target,
        target_date=target,
        target_source=TargetSource.AUTO,
        status=EnrollmentStatus.ACTIVE,
    )
    await enrollment_repo.add(session, enrollment)
    return enrollment, True


async def restart(
    session: AsyncSession, enrollment: TrackEnrollment, track: Track
) -> TrackEnrollment:
    """Move day one to today and recompute the dates.

    Progress is NOT cleared. Somebody who fell behind wants a realistic deadline,
    not to lose the twelve lessons they finished - and if they did want that,
    deleting progress is a different, louder decision.
    """
    weeks = await duration_weeks(session, track)
    now = utcnow()
    target = auto_target_date(now, weeks)

    enrollment.started_at = now
    enrollment.auto_target_date = target
    # A manual date is dropped here on purpose: it was chosen relative to the
    # old start, so keeping it would silently mean something different.
    enrollment.target_date = target
    enrollment.target_source = TargetSource.AUTO
    enrollment.status = EnrollmentStatus.ACTIVE
    enrollment.completed_at = None
    return enrollment


def set_target_date(
    enrollment: TrackEnrollment, target: date | None
) -> TrackEnrollment:
    """`None` restores the roadmap's own suggestion."""
    if target is None:
        enrollment.target_date = enrollment.auto_target_date
        enrollment.target_source = TargetSource.AUTO
    else:
        enrollment.target_date = target
        enrollment.target_source = TargetSource.MANUAL
    return enrollment


@dataclass(frozen=True)
class EnrollmentState:
    """The full picture for one user and one track."""

    status: str
    duration_weeks: int
    started_at: datetime | None = None
    target_date: date | None = None
    auto_target_date: date | None = None
    target_source: str | None = None
    projected_target_date: date | None = None
    days_total: int = 0
    days_elapsed: int = 0
    days_remaining: int = 0
    is_overdue: bool = False
    expected_week: int = 0
    actual_week: int = 0
    behind_by_weeks: int = 0
    completed_at: datetime | None = None

    # What the track contains. The Start screen has to answer "what am I signing
    # up for" before somebody commits to twenty weeks of it.
    total_lessons: int = 0
    total_labs: int = 0
    total_quizzes: int = 0


async def describe(
    session: AsyncSession, user: User, track: Track
) -> EnrollmentState:
    """One place that answers "where is this person in this track"."""
    weeks = await duration_weeks(session, track)
    enrollment = await enrollment_repo.get(session, user.id, track.id)

    counts = {
        "total_lessons": await content_repo.count_lessons(session, track.id),
        "total_labs": await content_repo.count_labs(session, track.id),
        "total_quizzes": await quiz_repo.count_quizzes(session, track.id),
    }

    if enrollment is None:
        # Even un-started, the Start screen shows how long it would take and
        # when it would finish if pressed now.
        return EnrollmentState(
            status="not_started",
            duration_weeks=weeks,
            projected_target_date=auto_target_date(today(), weeks),
            **counts,
        )

    clock = countdown(enrollment.started_at, enrollment.target_date)
    expected = expected_week(enrollment.started_at)
    actual = await enrollment_repo.furthest_completed_week(session, user.id, track.id)

    return EnrollmentState(
        status=enrollment.status,
        duration_weeks=weeks,
        started_at=enrollment.started_at,
        target_date=enrollment.target_date,
        auto_target_date=enrollment.auto_target_date,
        target_source=enrollment.target_source,
        days_total=clock.days_total,
        days_elapsed=clock.days_elapsed,
        days_remaining=clock.days_remaining,
        is_overdue=clock.is_overdue and enrollment.status == EnrollmentStatus.ACTIVE,
        expected_week=min(expected, weeks) if weeks else expected,
        actual_week=actual,
        behind_by_weeks=behind_by_weeks(expected, actual),
        completed_at=enrollment.completed_at,
        **counts,
    )
