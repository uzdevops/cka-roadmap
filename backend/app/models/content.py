"""Curriculum content: Phase -> Week -> Lesson, plus Labs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.progress import LabProgress, LessonProgress
    from app.models.quiz import Quiz


class Track(Base, TimestampMixin):
    """One programme of study: a certification, a topic, or both.

    `is_topic` and `is_certificate` are two flags rather than one enum because
    several subjects are genuinely both - LFCS, CKA and AWS are each a topic
    somebody studies and an exam somebody sits. With a single `type` column the
    same content would have to exist twice and the two copies would drift.
    """

    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_title: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    provider: Mapped[str | None] = mapped_column(String(120), nullable=True)

    is_topic: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    is_certificate: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )

    # Exam metadata. Null on a track that is only a topic - there is no exam to
    # describe, and the UI must not render an exam panel for one.
    exam_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    exam_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Two characters for the rail mark, and the accent token used to tint it.
    mark: Mapped[str] = mapped_column(String(8), default="", nullable=False)
    accent: Mapped[str] = mapped_column(String(32), default="sky", nullable=False)

    # The official links for this track - what the resources page used to
    # hardcode for CKA.
    references: Mapped[list[Any]] = mapped_column(
        JSONB, default=list, nullable=False, server_default=text("'[]'::jsonb")
    )
    translations: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    phases: Mapped[list["Phase"]] = relationship(
        back_populates="track",
        cascade="all, delete-orphan",
        order_by="Phase.order_index",
    )


class Phase(Base, TimestampMixin):
    """One phase of a track's roadmap."""

    __tablename__ = "phases"
    __table_args__ = (UniqueConstraint("track_id", "slug", name="uq_phases_track_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    # Unique per track, not globally: "foundations" is a reasonable phase name
    # in every one of them.
    slug: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
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

    track: Mapped["Track"] = relationship(back_populates="phases")
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
    __table_args__ = (
        UniqueConstraint("track_id", "number", name="uq_weeks_track_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Denormalised from phase.track_id: week numbers are looked up directly
    # ("week 7 of this track") without a phase in hand, and the unique
    # constraint has to live on this table.
    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    phase_id: Mapped[int] = mapped_column(
        ForeignKey("phases.id", ondelete="CASCADE"), index=True, nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
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
