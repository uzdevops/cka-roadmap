"""link a web account to a Telegram chat

Deep linking rather than asking somebody to paste a code: they press a button on
the site, Telegram opens with `/start <token>` already filled in, and the bot
knows which account is being claimed.

`telegram_chat_id` is UNIQUE. One Telegram account belongs to one web account -
without that, two people sharing a phone (or one person with two logins) could
both point at the same chat, and the daily reminder would be sent about somebody
else's progress.

The token table is deliberately separate from `users` rather than three more
nullable columns there: a token is short-lived and single-use, and keeping the
history of attempts out of the account row means expiring one is a delete, not
an update to the user.

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-19 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "telegram_link_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_telegram_link_tokens_token", "telegram_link_tokens", ["token"], unique=True
    )
    op.create_index(
        "ix_telegram_link_tokens_user_id", "telegram_link_tokens", ["user_id"]
    )

    # BigInteger: Telegram chat ids already exceed 32 bits.
    op.add_column("users", sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True))
    op.add_column(
        "users", sa.Column("telegram_username", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column("telegram_linked_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Unique but nullable, so every unlinked account coexists happily - NULLs do
    # not collide in a unique index.
    op.create_index(
        "ix_users_telegram_chat_id", "users", ["telegram_chat_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_users_telegram_chat_id", table_name="users")
    op.drop_column("users", "telegram_linked_at")
    op.drop_column("users", "telegram_username")
    op.drop_column("users", "telegram_chat_id")

    op.drop_index("ix_telegram_link_tokens_user_id", table_name="telegram_link_tokens")
    op.drop_index("ix_telegram_link_tokens_token", table_name="telegram_link_tokens")
    op.drop_table("telegram_link_tokens")
