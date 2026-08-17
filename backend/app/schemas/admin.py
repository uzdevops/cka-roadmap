"""Admin CRUD payloads."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.quiz import QuestionWrite


class LessonCreate(BaseModel):
    week_id: int
    slug: str = Field(min_length=1, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=1, max_length=255)
    summary: str = ""
    content: str = ""
    order_index: int = 0
    estimated_minutes: int = 30
    day_of_week: int | None = Field(default=None, ge=1, le=7)
    is_published: bool = True


class LessonUpdate(BaseModel):
    week_id: int | None = None
    # {"uz": {"title": ..., "summary": ..., "content": ...}}
    translations: dict[str, Any] | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    summary: str | None = None
    content: str | None = None
    order_index: int | None = None
    estimated_minutes: int | None = None
    day_of_week: int | None = Field(default=None, ge=1, le=7)
    is_published: bool | None = None


class QuizCreate(BaseModel):
    phase_id: int
    week_id: int | None = None
    slug: str = Field(min_length=1, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    pass_score: float = 70.0
    time_limit_minutes: int | None = None
    order_index: int = 0
    is_published: bool = True
    questions: list[QuestionWrite] = Field(default_factory=list)


class QuizUpdate(BaseModel):
    translations: dict[str, Any] | None = None
    title: str | None = None
    description: str | None = None
    pass_score: float | None = None
    time_limit_minutes: int | None = None
    order_index: int | None = None
    is_published: bool | None = None
    questions: list[QuestionWrite] | None = None


class LabCreate(BaseModel):
    phase_id: int
    week_id: int | None = None
    slug: str = Field(min_length=1, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    scenario: str = ""
    difficulty: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")
    estimated_minutes: int = 45
    environment_setup: str = ""
    cleanup: str = ""
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    order_index: int = 0
    is_published: bool = True


class LabUpdate(BaseModel):
    translations: dict[str, Any] | None = None
    title: str | None = None
    description: str | None = None
    scenario: str | None = None
    difficulty: str | None = Field(default=None, pattern="^(beginner|intermediate|advanced)$")
    estimated_minutes: int | None = None
    environment_setup: str | None = None
    cleanup: str | None = None
    tasks: list[dict[str, Any]] | None = None
    order_index: int | None = None
    is_published: bool | None = None


class AdminLessonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    week_id: int
    slug: str
    title: str
    summary: str
    content: str
    order_index: int
    estimated_minutes: int
    day_of_week: int | None
    is_published: bool
    is_placeholder: bool
    translations: dict[str, Any] = Field(default_factory=dict)


class AdminQuizRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phase_id: int
    week_id: int | None
    slug: str
    title: str
    description: str
    pass_score: float
    time_limit_minutes: int | None
    order_index: int
    is_published: bool
    translations: dict[str, Any] = Field(default_factory=dict)
    questions: list[QuestionWrite] = Field(default_factory=list)


class AdminLabRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phase_id: int
    week_id: int | None
    slug: str
    title: str
    description: str
    scenario: str
    difficulty: str
    estimated_minutes: int
    environment_setup: str
    cleanup: str
    tasks: list[dict[str, Any]]
    order_index: int
    is_published: bool
    translations: dict[str, Any] = Field(default_factory=dict)


class AdminStats(BaseModel):
    users: int
    students: int
    admins: int
    phases: int
    weeks: int
    lessons: int
    quizzes: int
    questions: int
    labs: int
    quiz_attempts: int
    completed_lessons: int
