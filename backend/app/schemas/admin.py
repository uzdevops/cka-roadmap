"""Admin CRUD payloads."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.quiz import QuestionWrite


class LessonCreate(BaseModel):
    week_id: int
    slug: str = Field(min_length=1, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=1, max_length=255)
    summary: str = ""
    content: str = ""
    # A YouTube link, shown as a player above the lesson.
    video_url: str | None = Field(default=None, max_length=512)
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
    video_url: str | None = Field(default=None, max_length=512)
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
    video_url: str | None = None
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


# --- Users ---------------------------------------------------------------


class AdminUserRead(BaseModel):
    """A user plus the progress numbers the admin list shows."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str | None = None
    full_name: str | None
    role: str
    is_active: bool
    # The two checkboxes, and the name their combination is shown under.
    access_topics: bool = True
    access_certificates: bool = True
    role_label: str = ""
    created_at: datetime
    last_active: date | None = None

    completed_lessons: int = 0
    total_lessons: int = 0
    progress_percent: float = 0.0
    quiz_attempts: int = 0
    quiz_average: float | None = None
    completed_labs: int = 0
    current_streak: int = 0


class AdminUserCreate(BaseModel):
    email: EmailStr
    username: str | None = Field(default=None, min_length=1, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    role: Literal["student", "admin"] = "student"
    # Independent grants rather than one role name, because the content
    # categories overlap. Both default on, which is "Full Student".
    access_topics: bool = True
    access_certificates: bool = True


class AdminUserUpdate(BaseModel):
    """Every field optional: this is a PATCH, and an omitted key means 'leave it'."""

    full_name: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, min_length=1, max_length=64)
    role: Literal["student", "admin"] | None = None
    is_active: bool | None = None
    access_topics: bool | None = None
    access_certificates: bool | None = None
    # Registration is closed, so resetting a forgotten password is an admin job.
    password: str | None = Field(default=None, min_length=8, max_length=128)
