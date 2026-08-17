"""add per-locale translations to content tables

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-02 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# English stays in the base columns; these hold only the overrides.
TABLES = ("phases", "weeks", "lessons", "labs", "quizzes", "questions")


def upgrade() -> None:
    for table in TABLES:
        op.add_column(
            table,
            sa.Column(
                "translations",
                postgresql.JSONB(astext_type=sa.Text()),
                server_default="{}",
                nullable=False,
            ),
        )


def downgrade() -> None:
    for table in TABLES:
        op.drop_column(table, "translations")
