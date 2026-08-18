"""Curriculum content: Phase -> Week -> Lesson, plus Labs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.progress import LabProgress, LessonProgress
    from app.models.quiz import Quiz


class Phase(Base, TimestampMixin):
    """One of the six CKA roadmap phases."""

    __tablename__ = "phases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)

    # CKA exam domain metadata (used for the readiness estimate)
    exam_domain: Mapped[str | None] = mapped_column(String(120), nullable=True)
    exam_weight: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    week_start: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    week_end: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    color: Mapped[str] = mapped_column(String(32), default="sky", nullable=False)
    # Per-locale overrides; English lives in the columns above.
    translations: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    weeks: Mapped[list["Week"]] = relationship(
        back_populates="phase",
        cascade="all, delete-orphan",
        order_by="Week.order_index",
    )
    quizzes: Mapped[list["Quiz"]] = relationship(
        back_populates="phase", cascade="all, delete-orphan"
    )
    labs: Mapped[list["Lab"]] = relationship(
        back_populates="phase", cascade="all, delete-orphan"
    )


class Week(Base, TimestampMixin):
    __tablename__ = "weeks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phase_id: Mapped[int] = mapped_column(
        ForeignKey("phases.id", ondelete="CASCADE"), index=True, nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Per-locale overrides; English lives in the columns above.
    translations: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    phase: Mapped["Phase"] = relationship(back_populates="weeks")
    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="week",
        cascade="all, delete-orphan",
        order_by="Lesson.order_index",
    )


class Lesson(Base, TimestampMixin):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_id: Mapped[int] = mapped_column(
        ForeignKey("weeks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    # 1=Mon .. 6=Sat (lab day), 7=Sun (review)
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_placeholder: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # [{"title": ..., "url": ...}] - official documentation for this topic,
    # shown at the end of the lesson. Structured rather than written into the
    # body so it survives an edit and works for generated placeholder lessons.
    references: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    # Per-locale overrides; English lives in the columns above.
    translations: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    week: Mapped["Week"] = relationship(back_populates="lessons")
    quizzes: Mapped[list["Quiz"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan"
    )
    progress: Mapped[list["LessonProgress"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan"
    )


class Lab(Base, TimestampMixin):
    __tablename__ = "labs"

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
    scenario: Mapped[str] = mapped_column(Text, default="", nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="beginner", nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=45, nullable=False)
    environment_setup: Mapped[str] = mapped_column(Text, default="", nullable=False)
    cleanup: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # [{title, instructions, solution, verification}]
    tasks: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Per-locale overrides; English lives in the columns above.
    translations: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    phase: Mapped["Phase"] = relationship(back_populates="labs")
    progress: Mapped[list["LabProgress"]] = relationship(
        back_populates="lab", cascade="all, delete-orphan"
    )
