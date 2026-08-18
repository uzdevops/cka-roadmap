"""per-lesson documentation links

Structured rather than appended to the markdown body, so the links survive an
admin editing the lesson text and so a placeholder lesson - whose body the
seeder generates - can carry them too.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-18 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "lessons",
        sa.Column(
            "references",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("lessons", "references")
