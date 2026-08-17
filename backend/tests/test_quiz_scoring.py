"""Quiz scoring: command normalisation, fuzzy matching and end-to-end grading."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.config import settings
from app.models import Phase, Question, Quiz, Week
from app.services.quiz_service import (
    command_matches,
    grade_question,
    normalize_command,
)
from tests.conftest import auth_header, login

API = settings.api_v1_prefix


# --- Pure functions ------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("kubectl get pods", "kubectl get pods"),
        ("  kubectl   get    pods  ", "kubectl get pods"),
        ("$ kubectl get pods", "kubectl get pods"),
        ("KUBECTL GET PODS", "kubectl get pods"),
        ("kubectl get po", "kubectl get pods"),
        ("kubectl get deploy", "kubectl get deployments"),
        ("kubectl get pods -n kube-system", "kubectl get pods --namespace kube-system"),
        ("kubectl get pods --namespace=kube-system", "kubectl get pods --namespace kube-system"),
        ("kubectl get pods;", "kubectl get pods"),
        ("sudo kubectl get pods", "kubectl get pods"),
    ],
)
def test_normalize_command(raw: str, expected: str) -> None:
    assert normalize_command(raw) == expected


def test_command_matches_accepts_equivalent_forms() -> None:
    accepted = ["kubectl get events --sort-by=.lastTimestamp"]
    assert command_matches("kubectl get events --sort-by=.lastTimestamp", accepted)
    assert command_matches("  KUBECTL GET EV --sort-by .lastTimestamp ", accepted)
    assert command_matches("$ kubectl get events --sort-by='.lastTimestamp'", accepted)


def test_command_matches_tolerates_flag_order() -> None:
    accepted = ["kubectl logs api --previous"]
    assert command_matches("kubectl logs --previous api", accepted)


def test_command_matches_rejects_wrong_commands() -> None:
    accepted = ["kubectl get pods"]
    assert not command_matches("kubectl delete pods", accepted)
    assert not command_matches("", accepted)
    assert not command_matches("helm list", accepted)


def test_grade_single_choice_requires_exactly_one() -> None:
    q = Question(type="single_choice", correct_options=["b"], accepted_answers=[])
    assert grade_question(q, ["b"], None)
    assert not grade_question(q, ["a"], None)
    assert not grade_question(q, ["a", "b"], None)
    assert not grade_question(q, [], None)


def test_grade_multi_select_requires_exact_set() -> None:
    q = Question(type="multi_select", correct_options=["a", "c"], accepted_answers=[])
    assert grade_question(q, ["a", "c"], None)
    assert grade_question(q, ["c", "a"], None)      # order is irrelevant
    assert not grade_question(q, ["a"], None)       # no partial credit
    assert not grade_question(q, ["a", "b", "c"], None)


def test_grade_fill_command_uses_fuzzy_match() -> None:
    q = Question(
        type="fill_command",
        correct_options=[],
        accepted_answers=["kubectl get pods -o wide"],
    )
    assert grade_question(q, [], "kubectl get po -o wide")
    assert grade_question(q, [], "kubectl get pods --output wide")
    assert not grade_question(q, [], "kubectl describe pods")


# --- End to end through the API -----------------------------------------


async def _build_quiz(session) -> tuple[Quiz, list[int]]:
    """Returns the quiz plus its question ids in order (the relationship is
    not loaded eagerly, and lazy loading is unavailable on an async session)."""
    phase = Phase(
        slug="test-phase", title="Test Phase", description="", order_index=1,
        exam_weight=20, week_start=1, week_end=1,
    )
    session.add(phase)
    await session.flush()

    week = Week(phase_id=phase.id, number=1, title="Week 1", order_index=1)
    session.add(week)
    await session.flush()

    quiz = Quiz(
        phase_id=phase.id,
        week_id=week.id,
        slug="scoring-quiz",
        title="Scoring quiz",
        description="",
        pass_score=70.0,
        order_index=1,
    )
    session.add(quiz)
    await session.flush()

    questions = [
            Question(
                quiz_id=quiz.id, key="q1", type="single_choice",
                prompt="Which component schedules Pods?",
                options=[{"id": "a", "text": "kubelet"}, {"id": "b", "text": "kube-scheduler"}],
                correct_options=["b"], explanation="The scheduler.", points=1, order_index=1,
            ),
            Question(
                quiz_id=quiz.id, key="q2", type="multi_select",
                prompt="Which are control plane components?",
                options=[
                    {"id": "a", "text": "etcd"},
                    {"id": "b", "text": "kube-proxy"},
                    {"id": "c", "text": "kube-apiserver"},
                ],
                correct_options=["a", "c"], explanation="", points=2, order_index=2,
            ),
            Question(
                quiz_id=quiz.id, key="q3", type="fill_command",
                prompt="List pods in every namespace.",
                options=[], correct_options=[],
                accepted_answers=["kubectl get pods --all-namespaces", "kubectl get pods -A"],
                explanation="", points=2, order_index=3,
            ),
    ]
    session.add_all(questions)
    await session.commit()
    return quiz, [q.id for q in questions]


async def test_quiz_detail_never_leaks_the_answer_key(
    client: AsyncClient, session, student_user
) -> None:
    await _build_quiz(session)
    resp = await client.get(f"{API}/quizzes/scoring-quiz")
    assert resp.status_code == 200

    body = resp.json()
    assert body["question_count"] == 3
    for question in body["questions"]:
        assert "correct_options" not in question
        assert "accepted_answers" not in question
        assert "explanation" not in question


async def test_perfect_submission_scores_100(
    client: AsyncClient, session, student_user
) -> None:
    _, ids = await _build_quiz(session)
    token = await login(client, "student@test.local", "StudentPass123!")

    resp = await client.post(
        f"{API}/quizzes/scoring-quiz/submit",
        headers=auth_header(token),
        json={
            "answers": [
                {"question_id": ids[0], "selected_options": ["b"]},
                {"question_id": ids[1], "selected_options": ["c", "a"]},
                {"question_id": ids[2], "selected_options": [],
                 "text_answer": "kubectl get po -A"},
            ]
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["score"] == 100.0
    assert body["passed"] is True
    assert body["correct_count"] == 3
    assert body["earned_points"] == 5
    assert all(r["explanation"] is not None for r in body["results"])


async def test_partial_submission_is_weighted_by_points(
    client: AsyncClient, session, student_user
) -> None:
    _, ids = await _build_quiz(session)
    token = await login(client, "student@test.local", "StudentPass123!")

    resp = await client.post(
        f"{API}/quizzes/scoring-quiz/submit",
        headers=auth_header(token),
        json={
            "answers": [
                {"question_id": ids[0], "selected_options": ["b"]},   # 1 point
                {"question_id": ids[1], "selected_options": ["a"]},   # wrong, 0 of 2
                {"question_id": ids[2], "selected_options": [],
                 "text_answer": "kubectl describe nodes"},            # wrong, 0 of 2
            ]
        },
    )
    body = resp.json()
    assert body["earned_points"] == 1
    assert body["total_points"] == 5
    assert body["score"] == 20.0
    assert body["passed"] is False


async def test_unanswered_questions_count_as_wrong(
    client: AsyncClient, session, student_user
) -> None:
    _, ids = await _build_quiz(session)
    token = await login(client, "student@test.local", "StudentPass123!")

    resp = await client.post(
        f"{API}/quizzes/scoring-quiz/submit",
        headers=auth_header(token),
        json={"answers": [{"question_id": ids[0], "selected_options": ["b"]}]},
    )
    body = resp.json()
    assert body["correct_count"] == 1
    assert body["question_count"] == 3
    assert body["score"] == 20.0


async def test_submitting_requires_authentication(
    client: AsyncClient, session
) -> None:
    await _build_quiz(session)
    resp = await client.post(
        f"{API}/quizzes/scoring-quiz/submit", json={"answers": []}
    )
    assert resp.status_code == 401


async def test_attempt_is_recorded_and_listed(
    client: AsyncClient, session, student_user
) -> None:
    _, ids = await _build_quiz(session)
    token = await login(client, "student@test.local", "StudentPass123!")

    await client.post(
        f"{API}/quizzes/scoring-quiz/submit",
        headers=auth_header(token),
        json={"answers": [{"question_id": ids[0], "selected_options": ["b"]}]},
    )

    resp = await client.get(f"{API}/quizzes/attempts", headers=auth_header(token))
    assert resp.status_code == 200
    attempts = resp.json()
    assert len(attempts) == 1
    assert attempts[0]["quiz_slug"] == "scoring-quiz"
