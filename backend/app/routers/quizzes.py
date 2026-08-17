"""Quiz listing, taking and scoring."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentUser, Locale, SessionDep
from app.i18n import tr
from app.repositories import quiz_repo
from app.schemas.quiz import (
    AttemptSummary,
    QuestionPublic,
    QuizDetail,
    QuizResult,
    QuizSubmission,
    QuizSummary,
)
from app.services import quiz_service
from app.services.quiz_service import localized_options

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


def _summary(quiz, best, counts, locked_ids, locale: str) -> QuizSummary:
    return QuizSummary(
        id=quiz.id,
        slug=quiz.slug,
        title=tr(quiz, "title", locale),
        description=tr(quiz, "description", locale),
        pass_score=quiz.pass_score,
        time_limit_minutes=quiz.time_limit_minutes,
        order_index=quiz.order_index,
        question_count=len(quiz.questions),
        phase_slug=quiz.phase.slug if quiz.phase else None,
        best_score=best.get(quiz.id),
        attempt_count=counts.get(quiz.id, 0),
        locked=quiz.phase_id in locked_ids,
    )


@router.get("", response_model=list[QuizSummary])
async def list_quizzes(
    session: SessionDep, user: CurrentUser, locale: Locale, phase: str | None = None
) -> list[QuizSummary]:
    quizzes = await quiz_repo.list_quizzes(session, phase_slug=phase)
    best = await quiz_repo.best_scores(session, user.id) if user else {}
    counts = await quiz_repo.attempt_counts(session, user.id) if user else {}
    locked = await quiz_service.locked_phase_ids(session, user)
    return [_summary(q, best, counts, locked, locale) for q in quizzes]


@router.get("/attempts", response_model=list[AttemptSummary])
async def my_attempts(
    session: SessionDep, user: CurrentUser, locale: Locale
) -> list[AttemptSummary]:
    attempts = await quiz_repo.list_attempts(session, user.id)
    return [
        AttemptSummary(
            id=a.id,
            quiz_id=a.quiz_id,
            quiz_slug=a.quiz.slug if a.quiz else None,
            quiz_title=tr(a.quiz, "title", locale) if a.quiz else None,
            score=a.score,
            passed=a.passed,
            correct_count=a.correct_count,
            question_count=a.question_count,
            completed_at=a.completed_at,
        )
        for a in attempts
    ]


@router.get("/{slug}", response_model=QuizDetail)
async def get_quiz(
    slug: str, session: SessionDep, user: CurrentUser, locale: Locale
) -> QuizDetail:
    quiz = await quiz_repo.get_quiz_by_slug(session, slug)
    if quiz is None or not quiz.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found"
        )

    locked = await quiz_service.locked_phase_ids(session, user)
    if quiz.phase_id in locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Finish the previous phase to unlock this quiz",
        )

    best = await quiz_repo.best_scores(session, user.id) if user else {}
    counts = await quiz_repo.attempt_counts(session, user.id) if user else {}
    base = _summary(quiz, best, counts, locked, locale)

    # The answer key never leaves the server until the attempt is graded.
    questions = [
        QuestionPublic(
            id=q.id,
            type=q.type,
            prompt=tr(q, "prompt", locale),
            options=localized_options(q, locale),
            points=q.points,
            order_index=q.order_index,
        )
        for q in sorted(quiz.questions, key=lambda x: (x.order_index, x.id))
    ]
    return QuizDetail(**base.model_dump(), questions=questions)


@router.post("/{slug}/submit", response_model=QuizResult)
async def submit_quiz(
    slug: str, payload: QuizSubmission, session: SessionDep, user: CurrentUser,
    locale: Locale,
) -> QuizResult:
    quiz = await quiz_repo.get_quiz_by_slug(session, slug)
    if quiz is None or not quiz.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found"
        )
    locked = await quiz_service.locked_phase_ids(session, user)
    if quiz.phase_id in locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Finish the previous phase to unlock this quiz",
        )
    return await quiz_service.score_submission(session, user, quiz, payload, locale)
