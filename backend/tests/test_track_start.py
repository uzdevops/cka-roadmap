"""Pressing Start, and the countdown that follows.

`ENFORCE_TRACK_START` is on in production and off for the rest of this suite -
almost every other test predates it and is about something else. This file turns
it on, which is the whole point: a flag nothing exercises is a flag that breaks
silently on the day it is switched on. ENFORCE_PHASE_UNLOCK already taught that
lesson here once.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Lesson, Phase, Track, TrackEnrollment, User, Week
from app.repositories import enrollment_repo
from app.services import enrollment_service
from tests.conftest import auth_header, login

API = settings.api_v1_prefix


async def _track(
    session: AsyncSession,
    slug: str,
    *,
    order: int = 0,
    week_end: int | None = 20,
    weeks: int = 0,
) -> Track:
    """A track with an optional phase declaring its length.

    `week_end=None` builds a track whose phase declares no range, so the service
    has to fall back to counting weeks, then to the configured default.
    """
    track = Track(slug=slug, title=slug.upper(), is_topic=True, order_index=order)
    session.add(track)
    await session.flush()

    if week_end is not None or weeks:
        phase = Phase(
            track_id=track.id, slug="foundations", title=f"{slug} phase",
            description="", order_index=1, exam_weight=10,
            week_start=1, week_end=week_end or 0,
        )
        session.add(phase)
        await session.flush()
        for i in range(1, weeks + 1):
            session.add(
                Week(
                    track_id=track.id, phase_id=phase.id, number=i,
                    title=f"week {i}", description="", order_index=i,
                )
            )
    await session.commit()
    return track


# --- the arithmetic, with no database in the way ----------------------------


def test_the_target_is_the_start_date_plus_the_roadmap() -> None:
    started = datetime(2026, 1, 1, 23, 50, tzinfo=timezone.utc)
    assert enrollment_service.auto_target_date(started, 20) == date(2026, 5, 21)


def test_the_target_is_anchored_on_the_date_not_the_clock() -> None:
    """Otherwise pressing Start at 23:50 buys you a day less than 00:10 does."""
    late = datetime(2026, 1, 1, 23, 50, tzinfo=timezone.utc)
    early = datetime(2026, 1, 1, 0, 10, tzinfo=timezone.utc)
    assert enrollment_service.auto_target_date(late, 20) == (
        enrollment_service.auto_target_date(early, 20)
    )


def test_day_one_is_week_one() -> None:
    """Not week zero - a person who starts today is in their first week, and
    "week 0 of 20" reads as a bug."""
    start = date(2026, 1, 1)
    assert enrollment_service.expected_week(start, on=start) == 1
    assert enrollment_service.expected_week(start, on=start + timedelta(days=6)) == 1
    assert enrollment_service.expected_week(start, on=start + timedelta(days=7)) == 2


def test_being_ahead_is_not_negative_lateness() -> None:
    assert enrollment_service.behind_by_weeks(expected=3, actual=6) == 0
    assert enrollment_service.behind_by_weeks(expected=6, actual=3) == 3


def test_days_remaining_goes_negative_and_flags_overdue() -> None:
    """The sign is the overdue signal the UI counts up from, so it is not
    clamped - unlike days_elapsed, which is."""
    start = date(2026, 1, 1)
    target = date(2026, 1, 11)
    clock = enrollment_service.countdown(start, target, on=date(2026, 1, 21))

    assert clock.days_remaining == -10
    assert clock.is_overdue is True
    assert clock.days_elapsed == 10, "elapsed should stop at the target, not run past it"
    assert clock.days_total == 10


# --- duration, and its fallbacks --------------------------------------------


async def test_duration_comes_from_the_phase_range(session: AsyncSession) -> None:
    track = await _track(session, "twenty", week_end=20)
    assert await enrollment_service.duration_weeks(session, track) == 20


async def test_duration_falls_back_to_counting_weeks(session: AsyncSession) -> None:
    """A track with structure but no declared range."""
    track = await _track(session, "counted", week_end=None, weeks=6)
    assert await enrollment_service.duration_weeks(session, track) == 6


async def test_duration_falls_back_to_the_configured_default(
    session: AsyncSession,
) -> None:
    """An empty track still needs a target date for its Start screen."""
    track = await _track(session, "empty", week_end=None, weeks=0)
    assert await enrollment_service.duration_weeks(session, track) == (
        settings.track_default_weeks
    )


# --- the endpoints ----------------------------------------------------------


async def test_enrollment_is_readable_before_starting(
    session: AsyncSession, student_client: AsyncClient
) -> None:
    """The Start screen has to answer "how long will this take" honestly."""
    await _track(session, "cka", week_end=20)

    response = await student_client.get(f"{API}/tracks/cka/enrollment")
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["status"] == "not_started"
    assert body["duration_weeks"] == 20
    assert body["projected_target_date"] is not None
    assert body["server_now"], "the client needs the server clock to avoid drift"


async def test_start_is_idempotent(
    session: AsyncSession, student_client: AsyncClient
) -> None:
    """A double-tapped button must not move somebody's day one - and is not an
    error worth showing either, so not a 409."""
    await _track(session, "cka", week_end=20)

    first = await student_client.post(f"{API}/tracks/cka/start")
    assert first.status_code == 201, first.text

    second = await student_client.post(f"{API}/tracks/cka/start")
    assert second.status_code == 201, second.text
    assert second.json()["started_at"] == first.json()["started_at"]
    assert second.json()["target_date"] == first.json()["target_date"]


async def test_starting_sets_a_twenty_week_target(
    session: AsyncSession, student_client: AsyncClient
) -> None:
    await _track(session, "cka", week_end=20)
    body = (await student_client.post(f"{API}/tracks/cka/start")).json()

    started = datetime.fromisoformat(body["started_at"]).date()
    target = date.fromisoformat(body["target_date"])
    assert (target - started).days == 140
    assert body["target_source"] == "auto"
    assert body["expected_week"] == 1


async def test_a_manual_target_date_and_back_again(
    session: AsyncSession, student_client: AsyncClient
) -> None:
    await _track(session, "cka", week_end=20)
    await student_client.post(f"{API}/tracks/cka/start")

    chosen = (date.today() + timedelta(days=60)).isoformat()
    manual = await student_client.patch(
        f"{API}/tracks/cka/enrollment", json={"target_date": chosen}
    )
    assert manual.status_code == 200, manual.text
    assert manual.json()["target_date"] == chosen
    assert manual.json()["target_source"] == "manual"

    # null restores the roadmap's own suggestion
    cleared = await student_client.patch(
        f"{API}/tracks/cka/enrollment", json={"target_date": None}
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["target_source"] == "auto"
    assert cleared.json()["target_date"] == cleared.json()["auto_target_date"]


async def test_restart_moves_day_one_and_keeps_progress(
    session: AsyncSession, student_user: User, student_client: AsyncClient
) -> None:
    track = await _track(session, "cka", week_end=20)

    # Started ten weeks ago, so the restart is visible.
    past = enrollment_service.utcnow() - timedelta(weeks=10)
    enrollment = TrackEnrollment(
        user_id=student_user.id, track_id=track.id, started_at=past,
        auto_target_date=enrollment_service.auto_target_date(past, 20),
        target_date=enrollment_service.auto_target_date(past, 20),
        target_source="auto", status="active",
    )
    session.add(enrollment)
    await session.commit()

    before = await student_client.get(f"{API}/tracks/cka/enrollment")
    assert before.json()["expected_week"] == 11

    restarted = await student_client.post(f"{API}/tracks/cka/restart")
    assert restarted.status_code == 200, restarted.text
    assert restarted.json()["expected_week"] == 1
    assert restarted.json()["target_source"] == "auto"


async def test_patch_and_restart_need_an_enrollment(
    session: AsyncSession, student_client: AsyncClient
) -> None:
    await _track(session, "cka", week_end=20)

    assert (await student_client.patch(
        f"{API}/tracks/cka/enrollment", json={"target_date": None}
    )).status_code == 404
    assert (await student_client.post(f"{API}/tracks/cka/restart")).status_code == 404


async def test_two_tracks_keep_independent_dates(
    session: AsyncSession, student_client: AsyncClient
) -> None:
    """The reason enrollments exist at all rather than one column on the user."""
    await _track(session, "cka", order=0, week_end=20)
    await _track(session, "lfcs", order=1, week_end=8)

    cka = (await student_client.post(f"{API}/tracks/cka/start")).json()
    assert (await student_client.get(f"{API}/tracks/lfcs/enrollment")).json()[
        "status"
    ] == "not_started", "starting cka must not start lfcs"

    lfcs = (await student_client.post(f"{API}/tracks/lfcs/start")).json()
    assert cka["target_date"] != lfcs["target_date"]
    assert cka["duration_weeks"] == 20
    assert lfcs["duration_weeks"] == 8


async def test_the_track_list_carries_a_compact_status(
    session: AsyncSession, student_client: AsyncClient
) -> None:
    """So the switcher needs one request, not one per track."""
    await _track(session, "cka", order=0, week_end=20)
    await _track(session, "lfcs", order=1, week_end=8)
    await student_client.post(f"{API}/tracks/cka/start")

    listing = await student_client.get(f"{API}/tracks")
    by_slug = {t["slug"]: t["enrollment"] for t in listing.json()}

    assert by_slug["cka"]["status"] == "active"
    assert by_slug["cka"]["current_week"] == 1
    assert by_slug["cka"]["duration_weeks"] == 20
    assert by_slug["lfcs"]["status"] == "not_started"


# --- the gate ---------------------------------------------------------------


@pytest.fixture
def enforce(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "enforce_track_start", True)


CONTENT_PATHS = ["/roadmap", "/roadmap/phases", "/lessons", "/labs", "/quizzes",
                 "/progress/dashboard", "/progress/overview"]


@pytest.mark.parametrize("path", CONTENT_PATHS)
async def test_content_is_refused_until_the_track_is_started(
    session: AsyncSession, student_client: AsyncClient, enforce: None, path: str
) -> None:
    await _track(session, "cka", week_end=20)

    response = await student_client.get(f"{API}{path}", params={"track": "cka"})
    assert response.status_code == 403, f"{path}: {response.text}"
    detail = response.json()["detail"]
    # A machine-readable code, because the frontend must tell "not started yet"
    # (show a Start button) apart from "not allowed" (show an error).
    assert detail["code"] == "track_not_started"
    assert detail["track"] == "cka"


@pytest.mark.parametrize("path", CONTENT_PATHS)
async def test_content_opens_once_started(
    session: AsyncSession, student_client: AsyncClient, enforce: None, path: str
) -> None:
    await _track(session, "cka", week_end=20)
    await student_client.post(f"{API}/tracks/cka/start")

    response = await student_client.get(f"{API}{path}", params={"track": "cka"})
    assert response.status_code == 200, f"{path}: {response.text}"


async def test_the_start_screen_itself_is_never_gated(
    session: AsyncSession, student_client: AsyncClient, enforce: None
) -> None:
    """It would be a locked door with the key behind it."""
    await _track(session, "cka", week_end=20)

    assert (await student_client.get(f"{API}/tracks")).status_code == 200
    assert (await student_client.get(f"{API}/tracks/cka/enrollment")).status_code == 200
    assert (await student_client.post(f"{API}/tracks/cka/start")).status_code == 201


async def test_an_admin_is_not_gated(
    session: AsyncSession, admin_client: AsyncClient, enforce: None
) -> None:
    """An admin inspecting content is not studying it."""
    await _track(session, "cka", week_end=20)

    response = await admin_client.get(f"{API}/lessons", params={"track": "cka"})
    assert response.status_code == 200, response.text


async def test_the_gate_is_off_when_the_flag_is_off(
    session: AsyncSession, student_client: AsyncClient
) -> None:
    """No `enforce` fixture here - this is the default the rest of the suite runs
    under, and it has to keep working for a deployment that wants every track
    open."""
    await _track(session, "cka", week_end=20)

    response = await student_client.get(f"{API}/lessons", params={"track": "cka"})
    assert response.status_code == 200, response.text


# --- lateness ---------------------------------------------------------------


async def test_behind_by_weeks_compares_the_calendar_with_the_lessons(
    session: AsyncSession, student_user: User, student_client: AsyncClient
) -> None:
    track = await _track(session, "cka", week_end=20, weeks=20)

    lesson = Lesson(
        week_id=(await enrollment_repo.count_weeks(session, track.id)) and
        (await session.execute(
            __import__("sqlalchemy").select(Week.id).where(
                Week.track_id == track.id, Week.number == 3
            )
        )).scalar_one(),
        slug="w3-lesson", title="Week 3 lesson", summary="", content="body",
        order_index=1, estimated_minutes=10, is_published=True, is_placeholder=False,
    )
    session.add(lesson)
    await session.flush()

    past = enrollment_service.utcnow() - timedelta(weeks=6)
    session.add(
        TrackEnrollment(
            user_id=student_user.id, track_id=track.id, started_at=past,
            auto_target_date=enrollment_service.auto_target_date(past, 20),
            target_date=enrollment_service.auto_target_date(past, 20),
            target_source="auto", status="active",
        )
    )
    from app.models import LessonProgress

    session.add(
        LessonProgress(user_id=student_user.id, lesson_id=lesson.id, completed=True)
    )
    await session.commit()

    body = (await student_client.get(f"{API}/tracks/cka/enrollment")).json()
    assert body["expected_week"] == 7, "six weeks in, they should be in week 7"
    assert body["actual_week"] == 3, "the furthest week they have finished a lesson in"
    assert body["behind_by_weeks"] == 4
