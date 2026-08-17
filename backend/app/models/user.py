"""User accounts and roles."""

from __future__ import annotations

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.progress import LabProgress, LessonProgress, StudyActivity
    from app.models.quiz import QuizAttempt


class UserRole(str, enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        String(20), default=UserRole.STUDENT.value, nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Profile / study plan
    target_exam_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    daily_study_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    # OAuth linkage (nullable: password accounts never populate these)
    oauth_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    oauth_subject: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    lesson_progress: Mapped[list["LessonProgress"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    lab_progress: Mapped[list["LabProgress"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    activities: Mapped[list["StudyActivity"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN.value
