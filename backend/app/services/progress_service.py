"""Streaks, dashboard aggregation and the exam-readiness estimate."""

from __future__ import annotations

from datetime import UTC, date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.i18n import DEFAULT_LOCALE, tr, verdict as verdict_for
from app.models import Track, User
from app.repositories import content_repo, enrollment_repo, progress_repo, quiz_repo
from app.schemas.progress import (
    DashboardResponse,
    ExamReadiness,
    PhaseProgress,
    QuizScorePoint,
    ReadinessBreakdown,
    StreakInfo,
)


def compute_streaks(days: list[date], today: date | None = None) -> StreakInfo:
    """Current streak counts back from today (or yesterday, if today is idle)."""
    if not days:
        return StreakInfo(current_streak=0, longest_streak=0, active_days=0, last_active=None)

    today = today or date.today()
    unique = sorted(set(days))

    longest = 1
    running = 1
    for prev, curr in zip(unique, unique[1:], strict=False):
        if (curr - prev).days == 1:
            running += 1
            longest = max(longest, running)
        else:
            running = 1

    last = unique[-1]
    gap = (today - last).days
    if gap > 1:
        current = 0
    else:
        current = 1
        cursor = last
        active = set(unique)
        while (cursor - timedelta(days=1)) in active:
            cursor -= timedelta(days=1)
            current += 1

    return StreakInfo(
        current_streak=current,
        longest_streak=longest,
        active_days=len(unique),
        last_active=last,
    )


def compute_readiness(
    phases: list[PhaseProgress], locale: str = DEFAULT_LOCALE
) -> ExamReadiness:
    """Quiz averages weighted by the exam domain percentages of ONE track.

    The scoping lives in the caller: this weights whatever phase list it is
    given, so it is only correct while that list belongs to a single track.

    Phases with no exam weight (Foundations, Mock Exams) are excluded from the
    weighting; a domain with no attempt yet contributes 0 but still counts
    against the total weight, so readiness only climbs as coverage grows.
    """
    breakdown: list[ReadinessBreakdown] = []
    weighted_sum = 0.0
    covered_weight = 0
    total_weight = sum(p.exam_weight for p in phases if p.exam_weight > 0)

    for phase in sorted(phases, key=lambda p: p.order_index):
        if phase.exam_weight <= 0:
            continue
        score = phase.quiz_average
        # A domain with no quiz data still counts against the total weight.
        effective = score if score is not None else 0.0
        # Lesson completion carries a quarter of the weight so that reading
        # (not just quizzing) moves the needle.
        blended = 0.75 * effective + 0.25 * phase.progress_percent
        contribution = (phase.exam_weight / total_weight) * blended if total_weight else 0.0
        weighted_sum += contribution
        if score is not None:
            covered_weight += phase.exam_weight
        breakdown.append(
            ReadinessBreakdown(
                domain=phase.phase_title,
                weight=phase.exam_weight,
                score=score,
                contribution=round(contribution, 2),
            )
        )

    score = round(weighted_sum, 2)
    if score >= 85:
        key = "ready"
    elif score >= 70:
        key = "almost"
    elif score >= 40:
        key = "progress"
    else:
        key = "early"

    return ExamReadiness(
        score=score,
        covered_weight=covered_weight,
        breakdown=breakdown,
        verdict=verdict_for(key, locale),
    )


async def build_dashboard(
    session: AsyncSession, track: Track, user: User, locale: str = DEFAULT_LOCALE
) -> DashboardResponse:
    # Every count below is per track. Unscoped, `compute_readiness` divides one
    # track's earned weight by every track's total weight, and somebody who has
    # finished the CKA reads about 17% ready - with no error anywhere.
    phases = await content_repo.list_phases(session, track.id)
    totals = await content_repo.total_lessons_per_phase(session, track.id)
    completed = await content_repo.completed_lessons_per_phase(
        session, user.id, track.id
    )
    phase_quiz_avg = await quiz_repo.best_score_per_phase(
        session, user.id, track.id
    )

    phase_progress: list[PhaseProgress] = []
    for phase in phases:
        total = totals.get(phase.id, 0)
        done = completed.get(phase.id, 0)
        avg = phase_quiz_avg.get(phase.id)
        phase_progress.append(
            PhaseProgress(
                phase_slug=phase.slug,
                phase_title=tr(phase, "title", locale),
                order_index=phase.order_index,
                exam_weight=phase.exam_weight,
                color=phase.color,
                total_lessons=total,
                completed_lessons=done,
                progress_percent=round((done / total) * 100, 1) if total else 0.0,
                quiz_average=round(avg, 1) if avg is not None else None,
            )
        )

    total_lessons = await content_repo.count_lessons(session, track.id)
    completed_lessons = await progress_repo.count_completed_lessons(
        session, user.id, track.id
    )
    total_labs = await content_repo.count_labs(session, track.id)
    completed_labs = await progress_repo.count_completed_labs(
        session, user.id, track.id
    )
    total_quizzes = await quiz_repo.count_quizzes(session, track.id)

    attempts = await quiz_repo.list_attempts(session, user.id, limit=30)
    best = await quiz_repo.best_scores(session, user.id)
    quiz_average = round(sum(best.values()) / len(best), 1) if best else None

    recent = [
        QuizScorePoint(
            attempt_id=a.id,
            quiz_slug=a.quiz.slug if a.quiz else "",
            quiz_title=tr(a.quiz, "title", locale) if a.quiz else "",
            score=a.score,
            completed_at=a.completed_at,
        )
        for a in reversed(attempts)
    ]

    streak = compute_streaks(await progress_repo.activity_days(session, user.id))
    readiness = compute_readiness(phase_progress, locale)

    # The exam date belongs to the enrollment for THIS track, not to the
    # account - somebody studying two tracks has two of them.
    enrollment = await enrollment_repo.get(session, user.id, track.id)
    target_exam_date = enrollment.target_date if enrollment else None
    days_until = (
        (target_exam_date - datetime_today()).days if target_exam_date else None
    )

    return DashboardResponse(
        total_lessons=total_lessons,
        completed_lessons=completed_lessons,
        overall_percent=round((completed_lessons / total_lessons) * 100, 1)
        if total_lessons
        else 0.0,
        total_labs=total_labs,
        completed_labs=completed_labs,
        total_quizzes=total_quizzes,
        attempted_quizzes=len(best),
        quiz_average=quiz_average,
        streak=streak,
        phases=phase_progress,
        recent_scores=recent,
        readiness=readiness,
        target_exam_date=target_exam_date,
        days_until_exam=days_until,
        daily_study_minutes=user.daily_study_minutes,
    )


def datetime_today() -> date:
    from datetime import datetime

    return datetime.now(UTC).date()
