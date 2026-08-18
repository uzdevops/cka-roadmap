"""The admin panel has to reach every quiz, including the ones students never
see in a list.

The student-facing list deliberately hides two kinds of quiz: unpublished
drafts, and lesson gates (a quiz with a `lesson_id`, taken from inside its
lesson). Those filters used to live inside the repository function, which the
admin router also called - so the admin panel could reach 20 of 78 quizzes and
the other 58 were uneditable, with nothing in the UI to say they existed.

These tests pin both views so the filters cannot drift back together.
"""

from __future__ import annotations

from httpx import AsyncClient

from app.config import settings
from app.models import Lesson, Phase, Question, Quiz, Week
from tests.conftest import ensure_track

API = settings.api_v1_prefix


async def _seed(session) -> dict[str, str]:
    """One of each kind of quiz: a lesson gate, a published standalone, a draft."""
    track = await ensure_track(session)
    phase = Phase(track_id=track.id, slug="p1", title="Phase 1", description="",
                  order_index=0, exam_weight=10, week_start=1, week_end=1)
    session.add(phase)
    await session.flush()

    week = Week(track_id=track.id, phase_id=phase.id, number=1, title="Week 1",
                description="", order_index=0)
    session.add(week)
    await session.flush()

    lesson = Lesson(week_id=week.id, slug="l1", title="Lesson one", summary="",
                    content="body", order_index=0, estimated_minutes=10,
                    is_published=True, is_placeholder=False)
    session.add(lesson)
    await session.flush()

    quizzes = {
        "gate": Quiz(phase_id=phase.id, week_id=week.id, lesson_id=lesson.id,
                     slug="l1-check", title="Lesson gate", description="",
                     pass_score=90.0, order_index=0, is_published=True),
        "standalone": Quiz(phase_id=phase.id, week_id=week.id, lesson_id=None,
                           slug="p1-review", title="Phase review", description="",
                           pass_score=70.0, order_index=1, is_published=True),
        "draft": Quiz(phase_id=phase.id, week_id=week.id, lesson_id=None,
                      slug="p1-draft", title="Unfinished", description="",
                      pass_score=70.0, order_index=2, is_published=False),
    }
    for quiz in quizzes.values():
        session.add(quiz)
    await session.flush()

    for quiz in quizzes.values():
        session.add(Question(
            quiz_id=quiz.id, key="q1", type="single_choice", prompt="Question?",
            options=[{"id": "a", "text": "right"}, {"id": "b", "text": "wrong"}],
            correct_options=["a"], accepted_answers=[], explanation="because",
            order_index=0, points=1,
        ))
    await session.commit()
    return {name: quiz.slug for name, quiz in quizzes.items()}


async def test_student_list_hides_gates_and_drafts(
    session, student_client: AsyncClient
) -> None:
    slugs = await _seed(session)

    response = await student_client.get(f"{API}/quizzes")
    assert response.status_code == 200
    listed = {q["slug"] for q in response.json()}

    assert listed == {slugs["standalone"]}, (
        "the roadmap list must show standalone published quizzes only - a lesson "
        "gate listed here would put the same questions in two places"
    )


async def test_admin_list_includes_gates_and_drafts(
    session, admin_client: AsyncClient
) -> None:
    slugs = await _seed(session)

    response = await admin_client.get(f"{API}/admin/quizzes")
    assert response.status_code == 200
    listed = {q["slug"] for q in response.json()}

    assert listed == set(slugs.values()), (
        f"admin must see every quiz; missing {set(slugs.values()) - listed}"
    )


async def test_admin_can_open_a_lesson_gate_for_editing(
    session, admin_client: AsyncClient
) -> None:
    """Listing it is not enough - the detail route has to serve it too."""
    slugs = await _seed(session)

    listing = await admin_client.get(f"{API}/admin/quizzes")
    gate = next(q for q in listing.json() if q["slug"] == slugs["gate"])

    detail = await admin_client.get(f"{API}/admin/quizzes/{gate['id']}")
    assert detail.status_code == 200
    assert detail.json()["slug"] == slugs["gate"]
