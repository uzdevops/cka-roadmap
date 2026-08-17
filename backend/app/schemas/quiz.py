"""Quiz schemas. Correct answers are never serialized to a student."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class QuestionOption(BaseModel):
    id: str
    text: str


class QuestionPublic(BaseModel):
    """What a student receives while taking the quiz - no answer key."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    prompt: str
    options: list[QuestionOption] = Field(default_factory=list)
    points: int = 1
    order_index: int = 0


class QuizSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str
    pass_score: float
    time_limit_minutes: int | None = None
    order_index: int
    question_count: int = 0
    phase_slug: str | None = None
    best_score: float | None = None
    attempt_count: int = 0
    locked: bool = False


class QuizDetail(QuizSummary):
    questions: list[QuestionPublic] = Field(default_factory=list)


class AnswerSubmission(BaseModel):
    question_id: int
    # Choice questions send option ids; fill_command sends a single string.
    selected_options: list[str] = Field(default_factory=list)
    text_answer: str | None = None


class QuizSubmission(BaseModel):
    answers: list[AnswerSubmission] = Field(default_factory=list)


class AnswerResult(BaseModel):
    question_id: int
    prompt: str
    type: str
    is_correct: bool
    points_earned: int
    points_possible: int
    given: list[str]
    correct: list[str]
    explanation: str = ""


class QuizResult(BaseModel):
    attempt_id: int
    quiz_slug: str
    quiz_title: str
    score: float
    passed: bool
    correct_count: int
    question_count: int
    earned_points: int
    total_points: int
    results: list[AnswerResult]
    completed_at: datetime | None = None


class AttemptSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quiz_id: int
    quiz_slug: str | None = None
    quiz_title: str | None = None
    score: float
    passed: bool
    correct_count: int
    question_count: int
    completed_at: datetime | None = None


# --- Admin-facing schemas (include the answer key) -----------------------


class QuestionWrite(BaseModel):
    key: str
    type: str = Field(pattern="^(single_choice|multi_select|fill_command)$")
    prompt: str
    options: list[dict[str, Any]] = Field(default_factory=list)
    correct_options: list[str] = Field(default_factory=list)
    accepted_answers: list[str] = Field(default_factory=list)
    explanation: str = ""
    points: int = 1
    order_index: int = 0
    # {"uz": {"prompt": ..., "explanation": ..., "options": [{"id","text"}]}}
    translations: dict[str, Any] = Field(default_factory=dict)
