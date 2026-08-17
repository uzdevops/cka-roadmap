"""initial schema

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- users ----------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=20), server_default="student", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("target_exam_date", sa.Date(), nullable=True),
        sa.Column("daily_study_minutes", sa.Integer(), server_default="60", nullable=False),
        sa.Column("oauth_provider", sa.String(length=32), nullable=True),
        sa.Column("oauth_subject", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_oauth_subject", "users", ["oauth_subject"])

    # --- phases ---------------------------------------------------------
    op.create_table(
        "phases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("exam_domain", sa.String(length=120), nullable=True),
        sa.Column("exam_weight", sa.Integer(), server_default="0", nullable=False),
        sa.Column("week_start", sa.Integer(), server_default="1", nullable=False),
        sa.Column("week_end", sa.Integer(), server_default="1", nullable=False),
        sa.Column("color", sa.String(length=32), server_default="sky", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_phases_slug", "phases", ["slug"], unique=True)
    op.create_index("ix_phases_order_index", "phases", ["order_index"])

    # --- weeks ----------------------------------------------------------
    op.create_table(
        "weeks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("phase_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["phase_id"], ["phases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_weeks_phase_id", "weeks", ["phase_id"])
    op.create_index("ix_weeks_number", "weeks", ["number"], unique=True)

    # --- lessons --------------------------------------------------------
    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("week_id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), server_default="", nullable=False),
        sa.Column("content", sa.Text(), server_default="", nullable=False),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), server_default="30", nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=True),
        sa.Column("is_published", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("is_placeholder", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["week_id"], ["weeks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lessons_week_id", "lessons", ["week_id"])
    op.create_index("ix_lessons_slug", "lessons", ["slug"], unique=True)
    op.create_index("ix_lessons_order_index", "lessons", ["order_index"])

    # --- labs -----------------------------------------------------------
    op.create_table(
        "labs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("phase_id", sa.Integer(), nullable=False),
        sa.Column("week_id", sa.Integer(), nullable=True),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("scenario", sa.Text(), server_default="", nullable=False),
        sa.Column("difficulty", sa.String(length=20), server_default="beginner", nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), server_default="45", nullable=False),
        sa.Column("environment_setup", sa.Text(), server_default="", nullable=False),
        sa.Column("cleanup", sa.Text(), server_default="", nullable=False),
        sa.Column("tasks", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["phase_id"], ["phases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["week_id"], ["weeks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_labs_phase_id", "labs", ["phase_id"])
    op.create_index("ix_labs_week_id", "labs", ["week_id"])
    op.create_index("ix_labs_slug", "labs", ["slug"], unique=True)

    # --- quizzes --------------------------------------------------------
    op.create_table(
        "quizzes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("phase_id", sa.Integer(), nullable=False),
        sa.Column("week_id", sa.Integer(), nullable=True),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("pass_score", sa.Float(), server_default="70", nullable=False),
        sa.Column("time_limit_minutes", sa.Integer(), nullable=True),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["phase_id"], ["phases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["week_id"], ["weeks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quizzes_phase_id", "quizzes", ["phase_id"])
    op.create_index("ix_quizzes_week_id", "quizzes", ["week_id"])
    op.create_index("ix_quizzes_slug", "quizzes", ["slug"], unique=True)

    # --- questions ------------------------------------------------------
    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quiz_id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("type", sa.String(length=32), server_default="single_choice", nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("correct_options", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("accepted_answers", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("explanation", sa.Text(), server_default="", nullable=False),
        sa.Column("points", sa.Integer(), server_default="1", nullable=False),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quiz_id", "key", name="uq_question_quiz_key"),
    )
    op.create_index("ix_questions_quiz_id", "questions", ["quiz_id"])

    # --- quiz_attempts --------------------------------------------------
    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("quiz_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), server_default="0", nullable=False),
        sa.Column("earned_points", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_points", sa.Integer(), server_default="0", nullable=False),
        sa.Column("correct_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("question_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("passed", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quiz_attempts_user_id", "quiz_attempts", ["user_id"])
    op.create_index("ix_quiz_attempts_quiz_id", "quiz_attempts", ["quiz_id"])

    # --- lesson_progress ------------------------------------------------
    op.create_table(
        "lesson_progress",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress_user_lesson"),
    )
    op.create_index("ix_lesson_progress_user_id", "lesson_progress", ["user_id"])
    op.create_index("ix_lesson_progress_lesson_id", "lesson_progress", ["lesson_id"])

    # --- lab_progress ---------------------------------------------------
    op.create_table(
        "lab_progress",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("lab_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="not_started", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "lab_id", name="uq_lab_progress_user_lab"),
    )
    op.create_index("ix_lab_progress_user_id", "lab_progress", ["user_id"])
    op.create_index("ix_lab_progress_lab_id", "lab_progress", ["lab_id"])

    # --- study_activity -------------------------------------------------
    op.create_table(
        "study_activity",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column("events", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "activity_date", name="uq_activity_user_date"),
    )
    op.create_index("ix_study_activity_user_id", "study_activity", ["user_id"])
    op.create_index("ix_study_activity_activity_date", "study_activity", ["activity_date"])


def downgrade() -> None:
    op.drop_table("study_activity")
    op.drop_table("lab_progress")
    op.drop_table("lesson_progress")
    op.drop_table("quiz_attempts")
    op.drop_table("questions")
    op.drop_table("quizzes")
    op.drop_table("labs")
    op.drop_table("lessons")
    op.drop_table("weeks")
    op.drop_table("phases")
    op.drop_table("users")
