"""Progress logic: streaks, lesson completion and the readiness estimate."""

from __future__ import annotations

from datetime import date, timedelta

from httpx import AsyncClient

from app.config import settings
from app.models import Lesson, Phase, Week
from app.schemas.progress import PhaseProgress
from app.services.progress_service import compute_readiness, compute_streaks
from tests.conftest import auth_header, ensure_track, login

API = settings.api_v1_prefix


# --- Streaks -------------------------------------------------------------


def test_streak_is_zero_without_activity() -> None:
    info = compute_streaks([])
    assert info.current_streak == 0
    assert info.longest_streak == 0
    assert info.last_active is None


def test_consecutive_days_build_a_streak() -> None:
    today = date(2026, 3, 10)
    days = [today - timedelta(days=n) for n in range(4)]
    info = compute_streaks(days, today=today)
    assert info.current_streak == 4
    assert info.longest_streak == 4
    assert info.active_days == 4


def test_yesterday_still_counts_as_an_active_streak() -> None:
    today = date(2026, 3, 10)
    days = [today - timedelta(days=1), today - timedelta(days=2)]
    info = compute_streaks(days, today=today)
    assert info.current_streak == 2


def test_a_two_day_gap_breaks_the_current_streak() -> None:
    today = date(2026, 3, 10)
    days = [today - timedelta(days=5), today - timedelta(days=4)]
    info = compute_streaks(days, today=today)
    assert info.current_streak == 0
    assert info.longest_streak == 2


def test_longest_streak_survives_a_later_gap() -> None:
    today = date(2026, 3, 20)
    days = [
        date(2026, 3, 1), date(2026, 3, 2), date(2026, 3, 3), date(2026, 3, 4),
        date(2026, 3, 19), date(2026, 3, 20),
    ]
    info = compute_streaks(days, today=today)
    assert info.longest_streak == 4
    assert info.current_streak == 2


def test_duplicate_days_are_collapsed() -> None:
    today = date(2026, 3, 10)
    days = [today, today, today - timedelta(days=1)]
    info = compute_streaks(days, today=today)
    assert info.active_days == 2
    assert info.current_streak == 2


# --- Readiness -----------------------------------------------------------


def _phase(order: int, weight: int, quiz_avg: float | None, percent: float) -> PhaseProgress:
    return PhaseProgress(
        phase_slug=f"p{order}",
        phase_title=f"Phase {order}",
        order_index=order,
        exam_weight=weight,
        total_lessons=10,
        completed_lessons=int(percent / 10),
        progress_percent=percent,
        quiz_average=quiz_avg,
    )


def test_readiness_ignores_zero_weight_phases() -> None:
    readiness = compute_readiness(
        [_phase(1, 0, 100.0, 100.0), _phase(2, 15, None, 0.0)]
    )
    assert [b.domain for b in readiness.breakdown] == ["Phase 2"]


def test_readiness_is_zero_with_no_progress() -> None:
    readiness = compute_readiness(
        [_phase(2, 15, None, 0.0), _phase(3, 30, None, 0.0)]
    )
    assert readiness.score == 0.0
    assert readiness.covered_weight == 0


def test_readiness_is_100_when_everything_is_perfect() -> None:
    phases = [
        _phase(2, 15, 100.0, 100.0),
        _phase(3, 30, 100.0, 100.0),
        _phase(4, 25, 100.0, 100.0),
        _phase(5, 30, 100.0, 100.0),
    ]
    readiness = compute_readiness(phases)
    assert readiness.score == 100.0
    assert readiness.covered_weight == 100
    assert "ready" in readiness.verdict.lower()


def test_readiness_weights_domains_by_exam_percentage() -> None:
    """Troubleshooting (30%) must move the needle twice as much as
    Workloads (15%) for the same score."""
    heavy = compute_readiness(
        [_phase(2, 15, 0.0, 0.0), _phase(5, 30, 100.0, 100.0)]
    )
    light = compute_readiness(
        [_phase(2, 15, 100.0, 100.0), _phase(5, 30, 0.0, 0.0)]
    )
    assert heavy.score > light.score
    assert round(heavy.score / light.score, 1) == 2.0


def test_readiness_blends_lessons_and_quizzes() -> None:
    """Quiz average carries 75% of a domain, lesson completion the other 25%."""
    quiz_only = compute_readiness([_phase(5, 30, 100.0, 0.0)])
    lessons_only = compute_readiness([_phase(5, 30, 0.0, 100.0)])
    assert quiz_only.score == 75.0
    assert lessons_only.score == 25.0


# --- Lesson completion end to end ----------------------------------------


async def _seed_lessons(session) -> None:
    track = await ensure_track(session)
    phase = Phase(
        track_id=track.id,
        slug="p1", title="Phase 1", description="", order_index=1,
        exam_weight=0, week_start=1, week_end=1,
    )
    session.add(phase)
    await session.flush()

    week = Week(track_id=track.id, phase_id=phase.id, number=1, title="Week 1",
                order_index=1)
    session.add(week)
    await session.flush()

    session.add_all(
        [
            Lesson(week_id=week.id, slug="lesson-one", title="Lesson one",
                   summary="", content="# one", order_index=1),
            Lesson(week_id=week.id, slug="lesson-two", title="Lesson two",
                   summary="", content="# two", order_index=2),
        ]
    )
    await session.commit()


async def test_marking_a_lesson_complete_updates_progress(
    client: AsyncClient, session, student_user
) -> None:
    await _seed_lessons(session)
    token = await login(client, "student", "StudentPass123!")

    resp = await client.post(
        f"{API}/lessons/lesson-one/complete", headers=auth_header(token)
    )
    assert resp.status_code == 200
    assert resp.json()["completed"] is True
    assert resp.json()["streak"] == 1

    overview = await client.get(f"{API}/progress/overview", headers=auth_header(token))
    body = overview.json()
    assert body["completed_lessons"] == 1
    assert body["total_lessons"] == 2
    assert body["percent"] == 50.0


async def test_completion_is_idempotent(
    client: AsyncClient, session, student_user
) -> None:
    await _seed_lessons(session)
    token = await login(client, "student", "StudentPass123!")

    for _ in range(3):
        await client.post(f"{API}/lessons/lesson-one/complete", headers=auth_header(token))

    overview = await client.get(f"{API}/progress/overview", headers=auth_header(token))
    assert overview.json()["completed_lessons"] == 1


async def test_completion_can_be_undone(
    client: AsyncClient, session, student_user
) -> None:
    await _seed_lessons(session)
    token = await login(client, "student", "StudentPass123!")

    await client.post(f"{API}/lessons/lesson-one/complete", headers=auth_header(token))
    resp = await client.delete(
        f"{API}/lessons/lesson-one/complete", headers=auth_header(token)
    )
    assert resp.status_code == 200
    assert resp.json()["completed"] is False

    overview = await client.get(f"{API}/progress/overview", headers=auth_header(token))
    assert overview.json()["completed_lessons"] == 0


async def test_lesson_detail_carries_prev_next_links(
    student_client: AsyncClient, session
) -> None:
    await _seed_lessons(session)

    first = (await student_client.get(f"{API}/lessons/lesson-one")).json()
    assert first["prev_slug"] is None
    assert first["next_slug"] == "lesson-two"

    second = (await student_client.get(f"{API}/lessons/lesson-two")).json()
    assert second["prev_slug"] == "lesson-one"
    assert second["next_slug"] is None


async def test_completing_a_lesson_requires_authentication(
    client: AsyncClient, session
) -> None:
    await _seed_lessons(session)
    resp = await client.post(f"{API}/lessons/lesson-one/complete")
    assert resp.status_code == 401


async def test_dashboard_reports_totals(
    client: AsyncClient, session, student_user
) -> None:
    await _seed_lessons(session)
    token = await login(client, "student", "StudentPass123!")
    await client.post(f"{API}/lessons/lesson-one/complete", headers=auth_header(token))

    resp = await client.get(f"{API}/progress/dashboard", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_lessons"] == 2
    assert body["completed_lessons"] == 1
    assert body["overall_percent"] == 50.0
    assert body["streak"]["current_streak"] == 1
    assert body["readiness"]["score"] == 0.0     # phase 1 carries no exam weight
