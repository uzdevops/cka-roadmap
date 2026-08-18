"""a video at the top of a lesson

Lessons get an optional YouTube link, rendered as a player above the prose.
Stored as a column rather than embedded in the markdown body for the same reason
`references` is: the seeder regenerates a placeholder lesson's body, so anything
written into that body is lost on the next redeploy, and an admin editing the
text should not be able to break the player by mistyping an embed.

Nullable: most lessons have no video, and an empty string would be a second way
to say the same thing.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-19 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("lessons", sa.Column("video_url", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("lessons", "video_url")
