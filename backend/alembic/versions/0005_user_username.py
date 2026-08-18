"""log in with a username, not only an email

The admin signs in as `admin`, not `admin@somewhere`. Email stays on the account
and still works for signing in; the username is simply a second identifier.

Existing rows are backfilled from the local part of their email so nobody loses
the ability to sign in, and so the unique index can be created without a
conflict. Collisions (a@x.com and a@y.com both wanting `a`) get a numeric
suffix, lowest id first.

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-18 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Strip anything outside the allowed set, fall back to "user" if that empties
# the string, then de-duplicate. Done in one statement so the column can be
# indexed immediately afterwards.
BACKFILL = """
UPDATE users AS u
SET username = c.candidate
FROM (
    SELECT
        id,
        CASE WHEN rn = 1 THEN base ELSE base || rn::text END AS candidate
    FROM (
        SELECT
            id,
            COALESCE(
                NULLIF(
                    lower(regexp_replace(split_part(email, '@', 1),
                                         '[^a-zA-Z0-9._-]', '', 'g')),
                    ''
                ),
                'user'
            ) AS base,
            row_number() OVER (
                PARTITION BY COALESCE(
                    NULLIF(
                        lower(regexp_replace(split_part(email, '@', 1),
                                             '[^a-zA-Z0-9._-]', '', 'g')),
                        ''
                    ),
                    'user'
                )
                ORDER BY id
            ) AS rn
        FROM users
    ) AS s
) AS c
WHERE u.id = c.id
"""


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(length=64), nullable=True))
    op.execute(BACKFILL)
    # Unique but nullable: an OAuth account created before its owner picks a
    # username has none, and NULLs do not collide in a unique index.
    op.create_index("ix_users_username", "users", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.drop_column("users", "username")
