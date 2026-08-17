"""Quiz scoring, including fuzzy matching for `kubectl` command answers."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from difflib import SequenceMatcher

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.i18n import DEFAULT_LOCALE, tr
from app.models import Question, QuestionType, Quiz, QuizAttempt, User
from app.repositories import progress_repo, quiz_repo
from app.schemas.quiz import AnswerResult, QuizResult, QuizSubmission

FUZZY_THRESHOLD = 0.90

# Shorthands the CLI itself accepts - normalizing them keeps grading fair.
_ALIASES = {
    "po": "pods",
    "pod": "pods",
    "deploy": "deployments",
    "deployment": "deployments",
    "svc": "services",
    "service": "services",
    "ns": "namespaces",
    "namespace": "namespaces",
    "no": "nodes",
    "node": "nodes",
    "cm": "configmaps",
    "configmap": "configmaps",
    "pv": "persistentvolumes",
    "pvc": "persistentvolumeclaims",
    "rs": "replicasets",
    "replicaset": "replicasets",
    "sts": "statefulsets",
    "statefulset": "statefulsets",
    "ds": "daemonsets",
    "daemonset": "daemonsets",
    "sa": "serviceaccounts",
    "serviceaccount": "serviceaccounts",
    "ing": "ingresses",
    "ingress": "ingresses",
    "secret": "secrets",
    "ep": "endpoints",
    "ev": "events",
    "event": "events",
    "job": "jobs",
    "cj": "cronjobs",
    "cronjob": "cronjobs",
    "-n": "--namespace",
    "-o": "--output",
    "-l": "--selector",
    "-f": "--filename",
    "-it": "-it",
}


def normalize_command(raw: str) -> str:
    """Reduce a shell command to a canonical, comparable form."""
    text = raw.strip()
    text = text.replace("\\\n", " ")
    # Drop a leading shell prompt and any sudo prefix.
    text = re.sub(r"^\s*[$#>]\s*", "", text)
    text = re.sub(r"^sudo\s+", "", text)
    text = text.rstrip(";& \t")
    text = text.lower()
    # `--flag=value` and `--flag value` must compare equal.
    text = re.sub(r"(--?[a-z0-9-]+)=", r"\1 ", text)
    tokens = [t for t in re.split(r"\s+", text) if t]
    tokens = [_ALIASES.get(t, t) for t in tokens]
    # Quoting style is irrelevant to correctness.
    tokens = [t.strip("'\"") for t in tokens]
    return " ".join(tokens)


def command_matches(given: str, accepted: list[str]) -> bool:
    if not given.strip():
        return False
    candidate = normalize_command(given)
    for answer in accepted:
        target = normalize_command(answer)
        if candidate == target:
            return True
        if SequenceMatcher(None, candidate, target).ratio() >= FUZZY_THRESHOLD:
            return True
        # Flag order should not decide correctness.
        if sorted(candidate.split()) == sorted(target.split()):
            return True
    return False


def grade_question(question: Question, given_options: list[str], text_answer: str | None) -> bool:
    if question.type == QuestionType.FILL_COMMAND.value:
        return command_matches(text_answer or "", list(question.accepted_answers or []))
    correct = {str(c) for c in (question.correct_options or [])}
    given = {str(g) for g in given_options}
    if question.type == QuestionType.SINGLE_CHOICE.value:
        return len(given) == 1 and given == correct
    return given == correct  # multi_select: exact set match, no partial credit


def localized_options(question: Question, locale: str) -> list[dict[str, str]]:
    """Option ids are the answer key, so only the visible text is translated."""
    options = list(question.options or [])
    translated = ((question.translations or {}).get(locale) or {}).get("options")
    if not translated:
        return options
    by_id = {str(o.get("id")): o.get("text") for o in translated if o.get("text")}
    return [{**o, "text": by_id.get(str(o.get("id")), o.get("text"))} for o in options]


async def score_submission(
    session: AsyncSession, user: User, quiz: Quiz, submission: QuizSubmission,
    locale: str = DEFAULT_LOCALE,
) -> QuizResult:
    if not quiz.questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Quiz has no questions"
        )

    by_id = {q.id: q for q in quiz.questions}
    answers = {a.question_id: a for a in submission.answers}

    results: list[AnswerResult] = []
    earned = 0
    total = 0
    correct_count = 0

    for question in sorted(quiz.questions, key=lambda q: (q.order_index, q.id)):
        total += question.points
        answer = answers.get(question.id)
        given_options = list(answer.selected_options) if answer else []
        text_answer = answer.text_answer if answer else None
        is_correct = grade_question(question, given_options, text_answer)
        if is_correct:
            earned += question.points
            correct_count += 1

        if question.type == QuestionType.FILL_COMMAND.value:
            given_display = [text_answer or ""]
            correct_display = list(question.accepted_answers or [])
        else:
            given_display = given_options
            correct_display = [str(c) for c in (question.correct_options or [])]

        results.append(
            AnswerResult(
                question_id=question.id,
                prompt=tr(question, "prompt", locale),
                type=question.type,
                is_correct=is_correct,
                points_earned=question.points if is_correct else 0,
                points_possible=question.points,
                given=given_display,
                correct=correct_display,
                explanation=tr(question, "explanation", locale),
            )
        )

    unknown = set(answers) - set(by_id)
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown question ids for this quiz: {sorted(unknown)}",
        )

    score = round((earned / total) * 100, 2) if total else 0.0
    now = datetime.now(UTC)
    attempt = QuizAttempt(
        user_id=user.id,
        quiz_id=quiz.id,
        score=score,
        earned_points=earned,
        total_points=total,
        correct_count=correct_count,
        question_count=len(quiz.questions),
        passed=score >= quiz.pass_score,
        details=[r.model_dump(mode="json") for r in results],
        completed_at=now,
    )
    await quiz_repo.add_attempt(session, attempt)
    await progress_repo.record_activity(session, user.id)
    await session.commit()

    return QuizResult(
        attempt_id=attempt.id,
        quiz_slug=quiz.slug,
        quiz_title=tr(quiz, "title", locale),
        score=score,
        passed=attempt.passed,
        correct_count=correct_count,
        question_count=len(quiz.questions),
        earned_points=earned,
        total_points=total,
        results=results,
        completed_at=now,
    )


async def locked_phase_ids(session: AsyncSession, user: User | None) -> set[int]:
    """Phase-unlock gate, active only when ENFORCE_PHASE_UNLOCK is on.

    A phase is locked until the previous phase's quiz average clears the
    configured minimum score.
    """
    from app.repositories import content_repo

    if not settings.enforce_phase_unlock:
        return set()

    phases = await content_repo.list_phases(session)
    if user is None:
        return {p.id for p in phases if p.order_index > 1}

    averages = await quiz_repo.best_score_per_phase(session, user.id)
    locked: set[int] = set()
    unlocked_through = 1
    for phase in sorted(phases, key=lambda p: p.order_index):
        if phase.order_index <= unlocked_through:
            avg = averages.get(phase.id)
            if avg is not None and avg >= settings.phase_unlock_min_score:
                unlocked_through = phase.order_index + 1
            continue
        locked.add(phase.id)
    return locked
