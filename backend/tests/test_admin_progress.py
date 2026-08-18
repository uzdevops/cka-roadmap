"""Where a user stands, broken down per track.

The admin list shows one overall percentage, which stops meaning much as soon as
somebody studies two programmes at once. This endpoint is the breakdown behind
it, and the numbers have to be attributed to the right track - the whole class of
bug this migration was about is a count that quietly includes another track's
rows.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import (
    Lesson,
    LessonProgress,
    Phase,
    Question,
    Quiz,
    QuizAttempt,
    Track,
    User,
    Week,
)

API = settings.api_v1_prefix


async def _track_with_lessons(
    session: AsyncSession, slug: str, order: int, lesson_count: int
) -> tuple[Track, list[Lesson], Quiz]:
    track = Track(slug=slug, title=slug.upper(), is_topic=True, order_index=order)
    session.add(track)
    await session.flush()

    phase = Phase(
        track_id=track.id, slug="foundations", title=f"{slug} phase",
        description="", order_index=1, exam_weight=10, week_start=1, week_end=1,
    )
    session.add(phase)
    await session.flush()

    week = Week(
        track_id=track.id, phase_id=phase.id, number=1,
        title=f"{slug} week", description="", order_index=1,
    )
    session.add(week)
    await session.flush()

    lessons = []
    for i in range(lesson_count):
        lesson = Lesson(
            week_id=week.id, slug=f"{slug}-lesson-{i}", title=f"{slug} lesson {i}",
            summary="", content="body", order_index=i, estimated_minutes=10,
            is_published=True, is_placeholder=False,
        )
        session.add(lesson)
        lessons.append(lesson)
    await session.flush()

    quiz = Quiz(
        phase_id=phase.id, week_id=week.id, slug=f"{slug}-quiz",
        title=f"{slug} quiz", description="", pass_score=70.0,
        order_index=0, is_published=True,
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
    await session.commit()
    return track, lessons, quiz


@pytest.fixture
async def scenario(session: AsyncSession, student_user: User) -> dict:
    """Two tracks. The student finishes 2 of 3 in alpha and nothing in beta,
    and attempts alpha's quiz twice - badly, then well."""
    alpha, alpha_lessons, alpha_quiz = await _track_with_lessons(session, "alpha", 0, 3)
    beta, _, beta_quiz = await _track_with_lessons(session, "beta", 1, 4)

    for lesson in alpha_lessons[:2]:
        session.add(
            LessonProgress(user_id=student_user.id, lesson_id=lesson.id, completed=True)
        )
    for score in (30.0, 90.0):
        session.add(
            QuizAttempt(
                user_id=student_user.id, quiz_id=alpha_quiz.id, score=score,
                correct_count=1, question_count=1, earned_points=1, total_points=1,
                passed=score >= 70.0, details=[],
            )
        )
    await session.commit()
    return {"alpha": alpha, "beta": beta, "user": student_user, "quiz": alpha_quiz}


async def test_progress_is_attributed_to_the_right_track(
    admin_client: AsyncClient, scenario: dict
) -> None:
    response = await admin_client.get(
        f"{API}/admin/users/{scenario['user'].id}/progress"
    )
    assert response.status_code == 200, response.text
    by_slug = {t["track_slug"]: t for t in response.json()["tracks"]}

    alpha = by_slug["alpha"]
    assert alpha["total_lessons"] == 3
    assert alpha["completed_lessons"] == 2
    assert alpha["progress_percent"] == pytest.approx(66.7, abs=0.1)

    beta = by_slug["beta"]
    assert beta["total_lessons"] == 4, "beta's total must not include alpha's lessons"
    assert beta["completed_lessons"] == 0, "alpha's completions leaked into beta"
    assert beta["progress_percent"] == 0.0


async def test_the_quiz_average_uses_the_best_attempt_not_the_mean(
    admin_client: AsyncClient, scenario: dict
) -> None:
    """Averaging every attempt would punish somebody for retaking a quiz, which
    is the opposite of what the platform asks people to do. 30 then 90 is a 90,
    not a 60.
    """
    response = await admin_client.get(
        f"{API}/admin/users/{scenario['user'].id}/progress"
    )
    alpha = next(t for t in response.json()["tracks"] if t["track_slug"] == "alpha")

    assert alpha["attempted_quizzes"] == 1, "one quiz, attempted twice"
    assert alpha["quiz_average"] == pytest.approx(90.0)


async def test_quiz_scores_report_attempts_and_the_pass_mark(
    admin_client: AsyncClient, scenario: dict
) -> None:
    response = await admin_client.get(
        f"{API}/admin/users/{scenario['user'].id}/progress"
    )
    scores = response.json()["quiz_scores"]

    assert len(scores) == 1, "only the attempted quiz should appear"
    score = scores[0]
    assert score["track_slug"] == "alpha"
    assert score["best_score"] == pytest.approx(90.0)
    assert score["attempts"] == 2
    assert score["passed"] is True


async def test_untouched_tracks_are_listed_with_zeroes(
    admin_client: AsyncClient, scenario: dict
) -> None:
    """Every track appears, so the admin can see what somebody has NOT started."""
    response = await admin_client.get(
        f"{API}/admin/users/{scenario['user'].id}/progress"
    )
    slugs = {t["track_slug"] for t in response.json()["tracks"]}
    assert {"alpha", "beta"} <= slugs


async def test_the_payload_carries_the_derived_role_label(
    admin_client: AsyncClient, scenario: dict
) -> None:
    response = await admin_client.get(
        f"{API}/admin/users/{scenario['user'].id}/progress"
    )
    assert response.json()["user"]["role_label"] == "Full Student"


async def test_a_missing_user_is_404(admin_client: AsyncClient) -> None:
    response = await admin_client.get(f"{API}/admin/users/999999/progress")
    assert response.status_code == 404


async def test_a_student_cannot_read_it(
    student_client: AsyncClient, scenario: dict
) -> None:
    response = await student_client.get(
        f"{API}/admin/users/{scenario['user'].id}/progress"
    )
    assert response.status_code == 403
