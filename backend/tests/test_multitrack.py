"""One track's content must never appear in another track's answers.

Every defect this file guards against is silent. Nothing raises when a query
forgets its track filter - the endpoint returns 200 with the wrong rows in it,
or a percentage quietly computed against the wrong denominator. Two tracks are
built here with deliberately COLLIDING structural keys (both have a phase called
"foundations" and both have a week 1) because that is exactly the shape the old
globally-unique constraints made impossible, and exactly the shape that breaks an
unscoped lookup.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Lab, Lesson, Phase, Question, Quiz, Track, Week

API = settings.api_v1_prefix


async def _build_track(session: AsyncSession, slug: str, order: int) -> Track:
    """A complete miniature track: phase -> week -> lesson, plus a quiz and a lab.

    The phase slug and the week number are identical across tracks on purpose.
    Lesson, quiz and lab slugs stay globally unique, which is the documented
    rule - they are prefixed with the track slug here for that reason.
    """
    track = Track(
        slug=slug,
        title=f"Track {slug}",
        is_topic=True,
        is_certificate=False,
        order_index=order,
    )
    session.add(track)
    await session.flush()

    phase = Phase(
        track_id=track.id,
        slug="foundations",          # same in both tracks
        title=f"{slug} foundations",
        description="",
        order_index=1,
        exam_weight=50,
        week_start=1,
        week_end=1,
    )
    session.add(phase)
    await session.flush()

    week = Week(
        track_id=track.id,
        phase_id=phase.id,
        number=1,                    # same in both tracks
        title=f"{slug} week 1",
        description="",
        order_index=1,
    )
    session.add(week)
    await session.flush()

    session.add(
        Lesson(
            week_id=week.id,
            slug=f"{slug}-lesson",
            title=f"{slug} lesson",
            summary="",
            content="body",
            order_index=1,
            estimated_minutes=10,
            is_published=True,
            is_placeholder=False,
        )
    )
    session.add(
        Lab(
            phase_id=phase.id,
            week_id=week.id,
            slug=f"{slug}-lab",
            title=f"{slug} lab",
            description="",
            difficulty="beginner",
            estimated_minutes=30,
            order_index=1,
            is_published=True,
        )
    )
    quiz = Quiz(
        phase_id=phase.id,
        week_id=week.id,
        lesson_id=None,
        slug=f"{slug}-quiz",
        title=f"{slug} quiz",
        description="",
        pass_score=70.0,
        order_index=1,
        is_published=True,
    )
    session.add(quiz)
    await session.flush()
    session.add(
        Question(
            quiz_id=quiz.id,
            key="q1",
            type="single_choice",
            prompt="Question?",
            options=[{"id": "a", "text": "right"}, {"id": "b", "text": "wrong"}],
            correct_options=["a"],
            accepted_answers=[],
            explanation="",
            order_index=0,
            points=1,
        )
    )
    await session.commit()
    return track


@pytest.fixture
async def two_tracks(session: AsyncSession) -> tuple[Track, Track]:
    a = await _build_track(session, "alpha", 0)
    b = await _build_track(session, "beta", 1)
    return a, b


# --- the collisions the old schema could not express ------------------------


async def test_two_tracks_can_share_a_week_number_and_phase_slug(
    two_tracks: tuple[Track, Track],
) -> None:
    """This is the whole reason for the migration.

    `weeks.number` was globally unique, and an integer cannot be namespaced by
    prefixing the way a slug can - so week 1 could exist exactly once on the
    platform. If the fixture built without an IntegrityError, that is fixed.
    """
    a, b = two_tracks
    assert a.id != b.id


# --- content endpoints ------------------------------------------------------


@pytest.mark.parametrize(
    "path,key",
    [
        ("/roadmap", None),
        ("/roadmap/phases", None),
        ("/lessons", "slug"),
        ("/labs", "slug"),
        ("/quizzes", "slug"),
    ],
)
async def test_listing_returns_only_the_requested_track(
    student_client: AsyncClient, two_tracks: tuple[Track, Track], path: str, key: str | None
) -> None:
    for wanted, other in (("alpha", "beta"), ("beta", "alpha")):
        response = await student_client.get(f"{API}{path}", params={"track": wanted})
        assert response.status_code == 200, response.text
        body = response.text
        assert f"{other}-" not in body and f"{other} " not in body, (
            f"{path}?track={wanted} leaked content from {other}: {body[:300]}"
        )


async def test_track_listing_carries_content_totals(
    student_client: AsyncClient, two_tracks: tuple[Track, Track]
) -> None:
    """The all-tracks grid prints lessons/labs/quizzes on every card, so the
    LIST payload has to carry the counts - a request per track would defeat it.
    Each fixture track holds exactly one of each, which also proves the grouped
    query does not smear one track's content across another."""
    response = await student_client.get(f"{API}/tracks")
    assert response.status_code == 200, response.text
    rows = {t["slug"]: t["enrollment"] for t in response.json()}
    for slug in ("alpha", "beta"):
        entry = rows[slug]
        assert entry["total_lessons"] == 1, entry
        assert entry["total_labs"] == 1, entry
        assert entry["total_quizzes"] == 1, entry


async def test_phase_slug_resolves_within_its_track(
    student_client: AsyncClient, two_tracks: tuple[Track, Track]
) -> None:
    """Both tracks have a phase called "foundations".

    Unscoped this is a `scalar_one_or_none` over two rows - a 500, not a 404.
    """
    for wanted in ("alpha", "beta"):
        response = await student_client.get(
            f"{API}/roadmap/phases/foundations", params={"track": wanted}
        )
        assert response.status_code == 200, response.text
        assert response.json()["title"] == f"{wanted} foundations"


async def test_week_number_resolves_within_its_track(
    student_client: AsyncClient, two_tracks: tuple[Track, Track]
) -> None:
    for wanted in ("alpha", "beta"):
        response = await student_client.get(
            f"{API}/roadmap/weeks/1/schedule", params={"track": wanted}
        )
        assert response.status_code == 200, response.text
        assert wanted in response.text
        other = "beta" if wanted == "alpha" else "alpha"
        assert other not in response.text


# --- counts and percentages -------------------------------------------------


async def test_dashboard_totals_count_one_track_only(
    student_client: AsyncClient, two_tracks: tuple[Track, Track]
) -> None:
    """The denominator bug: unscoped, one track's progress is divided by every
    track's totals, and a finished student reads a fraction of what they earned.
    """
    response = await student_client.get(
        f"{API}/progress/dashboard", params={"track": "alpha"}
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["total_lessons"] == 1, body["total_lessons"]
    assert body["total_labs"] == 1, body["total_labs"]
    assert body["total_quizzes"] == 1, body["total_quizzes"]
    assert len(body["phases"]) == 1


async def test_overview_counts_one_track_only(
    student_client: AsyncClient, two_tracks: tuple[Track, Track]
) -> None:
    response = await student_client.get(
        f"{API}/progress/overview", params={"track": "alpha"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["total_lessons"] == 1


# --- the track parameter itself ---------------------------------------------


async def test_unknown_track_is_404(
    student_client: AsyncClient, two_tracks: tuple[Track, Track]
) -> None:
    response = await student_client.get(f"{API}/lessons", params={"track": "nope"})
    assert response.status_code == 404


async def test_omitting_the_track_falls_back_to_the_first(
    student_client: AsyncClient, two_tracks: tuple[Track, Track]
) -> None:
    """Old clients that never send ?track= keep working - that is what lets the
    backend ship scoped before the frontend does."""
    default = await student_client.get(f"{API}/lessons")
    explicit = await student_client.get(f"{API}/lessons", params={"track": "alpha"})
    assert default.status_code == 200
    assert default.json() == explicit.json()


async def test_content_routes_still_require_authentication(
    client: AsyncClient, two_tracks: tuple[Track, Track]
) -> None:
    """The track dependency must not answer before the auth check does."""
    response = await client.get(f"{API}/lessons", params={"track": "alpha"})
    assert response.status_code == 401
