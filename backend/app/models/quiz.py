"""Quizzes, questions and attempts."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.content import Phase
    from app.models.user import User


class QuestionType(str, enum.Enum):
    SINGLE_CHOICE = "single_choice"
    MULTI_SELECT = "multi_select"
    FILL_COMMAND = "fill_command"


class Quiz(Base, TimestampMixin):
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phase_id: Mapped[int] = mapped_column(
        ForeignKey("phases.id", ondelete="CASCADE"), index=True, nullable=False
    )
    week_id: Mapped[int | None] = mapped_column(
        ForeignKey("weeks.id", ondelete="SET NULL"), index=True, nullable=True
    )
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    pass_score: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Per-locale overrides; English lives in the columns above.
    translations: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    phase: Mapped["Phase"] = relationship(back_populates="quizzes")
    questions: Mapped[list["Question"]] = relationship(
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="Question.order_index",
    )
    attempts: Mapped[list["QuizAttempt"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan"
    )


class Question(Base, TimestampMixin):
    __tablename__ = "questions"
    __table_args__ = (UniqueConstraint("quiz_id", "key", name="uq_question_quiz_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Stable authoring key -> lets the seeder upsert instead of duplicating.
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[str] = mapped_column(
        String(32), default=QuestionType.SINGLE_CHOICE.value, nullable=False
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    # [{"id": "a", "text": "..."}]
    options: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    # ["a", "c"] for choice questions
    correct_options: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    # ["kubectl get pods", ...] for fill_command questions
    accepted_answers: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Per-locale overrides; English lives in the columns above.
    translations: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    quiz: Mapped["Quiz"] = relationship(back_populates="questions")


class QuizAttempt(Base, TimestampMixin):
    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    quiz_id: Mapped[int] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    earned_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # [{question_id, given, correct, is_correct, explanation}]
    details: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="quiz_attempts")
    quiz: Mapped["Quiz"] = relationship(back_populates="attempts")
