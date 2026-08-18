"""The phase-unlock gate, which nothing else exercises.

`ENFORCE_PHASE_UNLOCK` defaults to False, so every other test in the suite runs
with this logic switched off. That is exactly why the cross-track bug in it was
invisible: the walk over phases used a single counter across the whole database,
and because each track numbers its phases from 1 they interleaved when sorted -
passing phase 1 of one track could unlock phase 2 of another, while a track that
sorted later stayed locked no matter what its owner scored.

Nothing raised. It would have shipped and broken on the day the flag was turned
on. These tests turn it on.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Phase, Question, Quiz, QuizAttempt, Track, User
from app.services import quiz_service


async def _track_with_phases(
    session: AsyncSession, slug: str, order: int, phase_count: int = 3
) -> tuple[Track, list[Phase]]:
    """A track whose phases are numbered from 1, like every other track."""
    track = Track(slug=slug, title=f"Track {slug}", is_topic=True, order_index=order)
    session.add(track)
    await session.flush()

    phases: list[Phase] = []
    for i in range(1, phase_count + 1):
        phase = Phase(
            track_id=track.id,
            slug=f"phase-{i}",
            title=f"{slug} phase {i}",
            description="",
            order_index=i,
            exam_weight=10,
            week_start=i,
            week_end=i,
        )
        session.add(phase)
        await session.flush()
        phases.append(phase)
    await session.commit()
    return track, phases


async def _pass_phase_quiz(
    session: AsyncSession, user: User, phase: Phase, score: float
) -> None:
    quiz = Quiz(
        phase_id=phase.id,
        slug=f"{phase.slug}-{phase.track_id}-quiz",
        title="Quiz",
        description="",
        pass_score=70.0,
        order_index=0,
        is_published=True,
    )
    session.add(quiz)
    await session.flush()
    session.add(
        Question(
            quiz_id=quiz.id, key="q1", type="single_choice", prompt="?",
            options=[{"id": "a", "text": "a"}], correct_options=["a"],
            accepted_answers=[], explanation="", order_index=0, points=1,
        )
    )
    session.add(
        QuizAttempt(
            user_id=user.id, quiz_id=quiz.id, score=score,
            correct_count=1, question_count=1,
            earned_points=1, total_points=1,
            passed=score >= quiz.pass_score, details=[],
        )
    )
    await session.commit()


@pytest.fixture(autouse=True)
def enforce(monkeypatch: pytest.MonkeyPatch) -> None:
    """The whole point of this file - the rest of the suite runs with it off."""
    monkeypatch.setattr(settings, "enforce_phase_unlock", True)


async def test_progress_in_one_track_does_not_unlock_another(
    session: AsyncSession, student_user: User
) -> None:
    """The bug, stated directly.

    The student passes phase 1 of track A and touches track B not at all. Track
    B's phase 2 must stay locked. Before the fix the two tracks' phases sorted
    into one sequence through a shared counter, so A's pass advanced B.
    """
    track_a, phases_a = await _track_with_phases(session, "alpha", 0)
    track_b, phases_b = await _track_with_phases(session, "beta", 1)

    await _pass_phase_quiz(session, student_user, phases_a[0], score=95.0)

    locked_b = await quiz_service.locked_phase_ids(session, student_user, track_b.id)

    assert phases_b[1].id in locked_b, (
        "passing a phase in track alpha unlocked phase 2 of track beta"
    )
    assert phases_b[2].id in locked_b


async def test_passing_unlocks_the_next_phase_of_the_same_track(
    session: AsyncSession, student_user: User
) -> None:
    """The gate still has to work - scoping it must not disable it."""
    track_a, phases_a = await _track_with_phases(session, "alpha", 0)
    await _track_with_phases(session, "beta", 1)

    before = await quiz_service.locked_phase_ids(session, student_user, track_a.id)
    assert phases_a[1].id in before, "phase 2 should start locked"

    await _pass_phase_quiz(session, student_user, phases_a[0], score=95.0)

    after = await quiz_service.locked_phase_ids(session, student_user, track_a.id)
    assert phases_a[1].id not in after, "phase 2 should unlock once phase 1 is passed"
    assert phases_a[2].id in after, "phase 3 should still be locked"


async def test_a_low_score_does_not_unlock(
    session: AsyncSession, student_user: User
) -> None:
    track_a, phases_a = await _track_with_phases(session, "alpha", 0)
    await _pass_phase_quiz(session, student_user, phases_a[0], score=40.0)

    locked = await quiz_service.locked_phase_ids(session, student_user, track_a.id)
    assert phases_a[1].id in locked


async def test_a_later_sorting_track_is_not_permanently_locked(
    session: AsyncSession, student_user: User
) -> None:
    """The other half of the interleaving bug.

    With one shared counter, a track whose phases sorted after another track's
    could never advance its own counter far enough, so its phase 2 stayed locked
    however well its owner did.
    """
    await _track_with_phases(session, "alpha", 0)
    track_b, phases_b = await _track_with_phases(session, "beta", 1)

    await _pass_phase_quiz(session, student_user, phases_b[0], score=95.0)

    locked_b = await quiz_service.locked_phase_ids(session, student_user, track_b.id)
    assert phases_b[1].id not in locked_b, (
        "beta's own pass did not unlock beta's phase 2"
    )
