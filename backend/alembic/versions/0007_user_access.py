"""who may see topics, and who may see certificates

Content splits into two categories that overlap: a track can be a topic, a
certificate, or both. Access is therefore two independent grants rather than one
role enum, which is also what makes the admin UI a pair of checkboxes.

The four names the product uses are derived from the pair, not stored:

    topics  certs   name
    ------  -----   ----
      x             DevOps Student
              x     Certificate Student
      x       x     Full Student
      (role = admin, both implied)  Administrator

Storing the names instead would mean "Full Student" is a third value that has to
be kept consistent with the other two everywhere it is checked, and renaming a
role would become a data migration.

Existing accounts get both grants: nobody loses access to content they can
already reach today.

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-19 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "access_topics", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "access_certificates",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "access_certificates")
    op.drop_column("users", "access_topics")
