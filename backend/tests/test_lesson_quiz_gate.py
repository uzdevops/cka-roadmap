"""A lesson with a quiz is finished by passing it, not by pressing a button."""

from __future__ import annotations

from httpx import AsyncClient

from app.config import settings
from app.models import Lesson, Phase, Question, Quiz, Week
from tests.conftest import ensure_track

API = settings.api_v1_prefix


async def _seed(session, *, with_quiz: bool, pass_score: float = 90.0):
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

    quiz = None
    if with_quiz:
        quiz = Quiz(phase_id=phase.id, week_id=week.id, lesson_id=lesson.id,
                    slug="l1-check", title="Check", description="",
                    pass_score=pass_score, order_index=0, is_published=True)
        session.add(quiz)
        await session.flush()
        # Ten one-point questions, so each is worth exactly 10%.
        for i in range(10):
            session.add(Question(
                quiz_id=quiz.id, key=f"q{i}", type="single_choice",
                prompt=f"Question {i}?",
                options=[{"id": "a", "text": "right"}, {"id": "b", "text": "wrong"}],
                correct_options=["a"], accepted_answers=[], explanation="because",
                points=1, order_index=i,
            ))
    await session.commit()
    return lesson, quiz


def _answers(questions, correct_count):
    return {"answers": [
        {"question_id": q["id"],
         "selected_options": ["a" if i < correct_count else "b"],
         "text_answer": None}
        for i, q in enumerate(questions)
    ]}


async def test_lesson_without_a_quiz_completes_with_the_button(
    student_client: AsyncClient, session
) -> None:
    await _seed(session, with_quiz=False)

    detail = (await student_client.get(f"{API}/lessons/l1")).json()
    assert detail["quiz_slug"] is None

    resp = await student_client.post(f"{API}/lessons/l1/complete")
    assert resp.status_code == 200
    assert resp.json()["completed"] is True


async def test_lesson_with_a_quiz_refuses_the_button(
    student_client: AsyncClient, session
) -> None:
    await _seed(session, with_quiz=True)

    detail = (await student_client.get(f"{API}/lessons/l1")).json()
    assert detail["quiz_slug"] == "l1-check"
    assert detail["quiz_pass_score"] == 90.0
    assert detail["quiz_passed"] is False
    assert detail["completed"] is False

    resp = await student_client.post(f"{API}/lessons/l1/complete")
    assert resp.status_code == 409
    assert "90%" in resp.json()["detail"]

    # And it really did not complete.
    assert (await student_client.get(f"{API}/lessons/l1")).json()["completed"] is False


async def test_below_the_pass_mark_does_not_complete_the_lesson(
    student_client: AsyncClient, session
) -> None:
    await _seed(session, with_quiz=True)
    quiz = (await student_client.get(f"{API}/quizzes/l1-check")).json()

    # 8 of 10 = 80%, under the 90% gate.
    result = (await student_client.post(
        f"{API}/quizzes/l1-check/submit", json=_answers(quiz["questions"], 8)
    )).json()
    assert result["score"] == 80.0

    detail = (await student_client.get(f"{API}/lessons/l1")).json()
    assert detail["completed"] is False
    assert detail["quiz_passed"] is False
    assert detail["quiz_best_score"] == 80.0
    assert detail["quiz_attempts"] == 1


async def test_passing_the_quiz_completes_the_lesson(
    student_client: AsyncClient, session
) -> None:
    await _seed(session, with_quiz=True)
    quiz = (await student_client.get(f"{API}/quizzes/l1-check")).json()

    result = (await student_client.post(
        f"{API}/quizzes/l1-check/submit", json=_answers(quiz["questions"], 9)
    )).json()
    assert result["score"] == 90.0

    detail = (await student_client.get(f"{API}/lessons/l1")).json()
    assert detail["completed"] is True, "90% is the pass mark, so it counts"
    assert detail["quiz_passed"] is True

    # The button works once the gate is behind you.
    assert (await student_client.post(f"{API}/lessons/l1/complete")).status_code == 200


async def test_the_result_says_which_answers_were_wrong(
    student_client: AsyncClient, session
) -> None:
    await _seed(session, with_quiz=True)
    quiz = (await student_client.get(f"{API}/quizzes/l1-check")).json()

    result = (await student_client.post(
        f"{API}/quizzes/l1-check/submit", json=_answers(quiz["questions"], 7)
    )).json()

    per_question = result["results"]
    assert len(per_question) == 10
    assert [r["is_correct"] for r in per_question] == [True] * 7 + [False] * 3
    wrong = next(r for r in per_question if not r["is_correct"])
    assert wrong["given"] == ["b"]
    assert wrong["correct"] == ["a"]
    assert wrong["explanation"] == "because"


async def test_best_score_is_kept_across_attempts(
    student_client: AsyncClient, session
) -> None:
    await _seed(session, with_quiz=True)
    quiz = (await student_client.get(f"{API}/quizzes/l1-check")).json()

    await student_client.post(f"{API}/quizzes/l1-check/submit", json=_answers(quiz["questions"], 10))
    await student_client.post(f"{API}/quizzes/l1-check/submit", json=_answers(quiz["questions"], 3))

    detail = (await student_client.get(f"{API}/lessons/l1")).json()
    assert detail["quiz_best_score"] == 100.0, "a worse retake must not undo a pass"
    assert detail["quiz_attempts"] == 2
    assert detail["completed"] is True
