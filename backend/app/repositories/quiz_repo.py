"""Quiz / question / attempt persistence."""

from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Phase, Question, Quiz, QuizAttempt


async def list_quizzes(session: AsyncSession, phase_slug: str | None = None) -> list[Quiz]:
    stmt = (
        select(Quiz)
        .join(Phase, Quiz.phase_id == Phase.id)
        .options(selectinload(Quiz.questions), selectinload(Quiz.phase))
        .where(Quiz.is_published.is_(True))
        .order_by(Phase.order_index, Quiz.order_index, Quiz.id)
    )
    if phase_slug:
        stmt = stmt.where(Phase.slug == phase_slug)
    return list((await session.execute(stmt)).scalars().unique().all())


async def get_quiz_by_slug(session: AsyncSession, slug: str) -> Quiz | None:
    stmt = (
        select(Quiz)
        .where(Quiz.slug == slug)
        .options(selectinload(Quiz.questions), selectinload(Quiz.phase))
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_quiz_by_id(session: AsyncSession, quiz_id: int) -> Quiz | None:
    stmt = (
        select(Quiz)
        .where(Quiz.id == quiz_id)
        .options(selectinload(Quiz.questions), selectinload(Quiz.phase))
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def add_attempt(session: AsyncSession, attempt: QuizAttempt) -> QuizAttempt:
    session.add(attempt)
    await session.flush()
    return attempt


async def list_attempts(
    session: AsyncSession, user_id: int, limit: int = 50
) -> list[QuizAttempt]:
    stmt = (
        select(QuizAttempt)
        .where(QuizAttempt.user_id == user_id)
        .options(selectinload(QuizAttempt.quiz))
        .order_by(desc(QuizAttempt.created_at))
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().unique().all())


async def best_scores(session: AsyncSession, user_id: int) -> dict[int, float]:
    stmt = (
        select(QuizAttempt.quiz_id, func.max(QuizAttempt.score))
        .where(QuizAttempt.user_id == user_id)
        .group_by(QuizAttempt.quiz_id)
    )
    return {qid: float(score) for qid, score in (await session.execute(stmt)).all()}


async def attempt_counts(session: AsyncSession, user_id: int) -> dict[int, int]:
    stmt = (
        select(QuizAttempt.quiz_id, func.count(QuizAttempt.id))
        .where(QuizAttempt.user_id == user_id)
        .group_by(QuizAttempt.quiz_id)
    )
    return {qid: int(count) for qid, count in (await session.execute(stmt)).all()}


async def best_score_per_phase(session: AsyncSession, user_id: int) -> dict[int, float]:
    """Average of the best score per quiz, grouped by phase."""
    best = (
        select(
            Quiz.phase_id.label("phase_id"),
            QuizAttempt.quiz_id.label("quiz_id"),
            func.max(QuizAttempt.score).label("best"),
        )
        .select_from(QuizAttempt)
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .where(QuizAttempt.user_id == user_id)
        .group_by(Quiz.phase_id, QuizAttempt.quiz_id)
        .subquery()
    )
    stmt = select(best.c.phase_id, func.avg(best.c.best)).group_by(best.c.phase_id)
    return {pid: float(avg) for pid, avg in (await session.execute(stmt)).all()}


async def count_quizzes(session: AsyncSession) -> int:
    stmt = select(func.count(Quiz.id)).where(Quiz.is_published.is_(True))
    return int((await session.execute(stmt)).scalar_one())


async def count_questions(session: AsyncSession) -> int:
    return int((await session.execute(select(func.count(Question.id)))).scalar_one())
