"""attach quizzes to lessons

A quiz with a lesson_id is the gate for finishing that lesson; one without it
stays the week/phase quiz it was before. Nullable, so every existing row keeps
working untouched.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-18 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("quizzes", sa.Column("lesson_id", sa.Integer(), nullable=True))
    op.create_index("ix_quizzes_lesson_id", "quizzes", ["lesson_id"])
    op.create_foreign_key(
        "fk_quizzes_lesson_id_lessons",
        "quizzes",
        "lessons",
        ["lesson_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_quizzes_lesson_id_lessons", "quizzes", type_="foreignkey")
    op.drop_index("ix_quizzes_lesson_id", table_name="quizzes")
    op.drop_column("quizzes", "lesson_id")
