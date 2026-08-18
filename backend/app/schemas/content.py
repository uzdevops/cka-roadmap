"""Roadmap / lesson / lab schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LessonSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    summary: str
    order_index: int
    estimated_minutes: int
    day_of_week: int | None = None
    is_placeholder: bool = False
    completed: bool = False


class LessonDetail(LessonSummary):
    content: str
    # Optional YouTube link, rendered as a player above the prose.
    video_url: str | None = None
    week_id: int
    week_number: int | None = None
    week_title: str | None = None
    phase_slug: str | None = None
    phase_title: str | None = None
    prev_slug: str | None = None
    next_slug: str | None = None
    # False when the body fell back to English for the requested locale.
    content_translated: bool = True

    # The gate on finishing this lesson. `quiz_slug` is null for a lesson that
    # has no quiz yet, and such a lesson is completed with a plain button.
    quiz_slug: str | None = None
    quiz_pass_score: float | None = None
    quiz_best_score: float | None = None
    quiz_passed: bool = False
    quiz_attempts: int = 0

    # Official documentation for the topic, shown at the end of the lesson.
    references: list[dict[str, str]] = Field(default_factory=list)


class WeekRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: int
    title: str
    description: str
    order_index: int
    lessons: list[LessonSummary] = Field(default_factory=list)
    completed_lessons: int = 0
    total_lessons: int = 0


class TrackRead(BaseModel):
    """One programme of study.

    `is_topic` and `is_certificate` are both sent because a track can be both,
    and the UI groups by them: exam chrome (pass marks, a countdown, a candidate
    handbook) only makes sense when `is_certificate` is true.
    """

    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    short_title: str
    summary: str = ""
    provider: str | None = None
    is_topic: bool
    is_certificate: bool
    exam_code: str | None = None
    exam_minutes: int | None = None
    mark: str = ""
    accent: str = "sky"
    references: list[dict] = []


class PhaseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str
    order_index: int
    exam_domain: str | None = None
    exam_weight: int = 0
    week_start: int
    week_end: int
    color: str = "sky"
    total_lessons: int = 0
    completed_lessons: int = 0
    progress_percent: float = 0.0
    locked: bool = False


class PhaseDetail(PhaseSummary):
    weeks: list[WeekRead] = Field(default_factory=list)
    quizzes: list["QuizSummary"] = Field(default_factory=list)
    labs: list["LabSummary"] = Field(default_factory=list)


class LabTask(BaseModel):
    title: str
    instructions: str
    solution: str = ""
    verification: str = ""


class LabSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str
    difficulty: str
    estimated_minutes: int
    order_index: int
    phase_slug: str | None = None
    status: str = "not_started"


class LabDetail(LabSummary):
    scenario: str
    environment_setup: str
    cleanup: str
    tasks: list[dict[str, Any]] = Field(default_factory=list)


class LabProgressUpdate(BaseModel):
    status: str = Field(pattern="^(not_started|in_progress|completed)$")


class LessonCompleteResponse(BaseModel):
    lesson_id: int
    completed: bool
    streak: int


class WeeklyScheduleDay(BaseModel):
    day: int
    label: str
    kind: str  # lesson | lab | review
    items: list[dict[str, Any]] = Field(default_factory=list)


class WeeklySchedule(BaseModel):
    week_number: int
    week_title: str
    phase_slug: str
    days: list[WeeklyScheduleDay]


# Imported at the bottom to resolve the forward references above.
from app.schemas.quiz import QuizSummary  # noqa: E402

PhaseDetail.model_rebuild()
