"""Dashboard / progress schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class PhaseProgress(BaseModel):
    phase_slug: str
    phase_title: str
    order_index: int
    exam_weight: int
    color: str = "sky"
    total_lessons: int
    completed_lessons: int
    progress_percent: float
    quiz_average: float | None = None


class QuizScorePoint(BaseModel):
    attempt_id: int
    quiz_slug: str
    quiz_title: str
    score: float
    completed_at: datetime | None = None


class StreakInfo(BaseModel):
    current_streak: int
    longest_streak: int
    active_days: int
    last_active: date | None = None


class ReadinessBreakdown(BaseModel):
    domain: str
    weight: int
    score: float | None
    contribution: float


class ExamReadiness(BaseModel):
    score: float
    covered_weight: int
    breakdown: list[ReadinessBreakdown] = Field(default_factory=list)
    verdict: str


class DashboardResponse(BaseModel):
    total_lessons: int
    completed_lessons: int
    overall_percent: float
    total_labs: int
    completed_labs: int
    total_quizzes: int
    attempted_quizzes: int
    quiz_average: float | None
    streak: StreakInfo
    phases: list[PhaseProgress]
    recent_scores: list[QuizScorePoint]
    readiness: ExamReadiness
    target_exam_date: date | None = None
    days_until_exam: int | None = None
    daily_study_minutes: int = 60
