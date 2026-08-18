"""one platform, many tracks

The whole roadmap used to be implicitly "the CKA roadmap": phases were the root,
week numbers were globally unique, and phase slugs were globally unique. A second
programme of study cannot exist under those rules - `weeks.number` is an integer,
so it cannot be namespaced by prefixing the way a slug could be, and "week 1"
can only exist once.

This adds `tracks`, hangs phases and weeks off it, and moves those two unique
constraints to be per-track. Existing content becomes the CKA track.

`is_topic` / `is_certificate` are two flags rather than one type, because LFCS,
CKA and AWS are each both a subject somebody studies and an exam somebody sits.

The order matters and the failure modes differ: dropping a unique index before
the backfill opens a window where duplicates are insertable, and setting NOT NULL
before the backfill fails on every existing row. Neither is recoverable halfway.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-18 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CKA_SLUG = "cka"


def upgrade() -> None:
    op.create_table(
        "tracks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("short_title", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("provider", sa.String(length=120), nullable=True),
        sa.Column(
            "is_topic", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "is_certificate",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("exam_code", sa.String(length=32), nullable=True),
        sa.Column("exam_minutes", sa.Integer(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "is_published", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("mark", sa.String(length=8), nullable=False, server_default=""),
        sa.Column("accent", sa.String(length=32), nullable=False, server_default="sky"),
        sa.Column(
            "references",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "translations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_tracks_slug", "tracks", ["slug"], unique=True)
    op.create_index("ix_tracks_order_index", "tracks", ["order_index"])
    op.create_index("ix_tracks_is_topic", "tracks", ["is_topic"])
    op.create_index("ix_tracks_is_certificate", "tracks", ["is_certificate"])

    # Everything that exists today is the CKA roadmap. Inserted here rather than
    # left to the seeder because the NOT NULL below needs a row to point at, and
    # a container that fails this migration never reaches the seeder.
    op.execute(
        sa.text(
            """
            INSERT INTO tracks (slug, title, short_title, summary, provider,
                                is_topic, is_certificate, exam_minutes,
                                order_index, mark, accent)
            VALUES (:slug, :title, :short, :summary, :provider,
                    true, true, 120, 0, 'K8', 'sky')
            """
        ).bindparams(
            slug=CKA_SLUG,
            title="Certified Kubernetes Administrator",
            short="CKA",
            summary=(
                "The twenty-week path to the CKA: cluster architecture, "
                "workloads, networking, storage, security and troubleshooting."
            ),
            provider="CNCF / Linux Foundation",
        )
    )

    # --- phases -------------------------------------------------------------
    op.add_column("phases", sa.Column("track_id", sa.Integer(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE phases SET track_id = (SELECT id FROM tracks WHERE slug = :slug)"
        ).bindparams(slug=CKA_SLUG)
    )
    op.alter_column("phases", "track_id", nullable=False)
    # RESTRICT, not CASCADE: phases cascade to weeks to lessons to every user's
    # progress, so one DELETE FROM tracks would wipe a certification's history
    # with no confirmation. Unpublish a track instead of deleting it.
    op.create_foreign_key(
        "fk_phases_track_id", "phases", "tracks", ["track_id"], ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_phases_track_id", "phases", ["track_id"])

    op.drop_index("ix_phases_slug", table_name="phases")
    op.create_index("ix_phases_slug", "phases", ["slug"])
    op.create_unique_constraint("uq_phases_track_slug", "phases", ["track_id", "slug"])

    # --- weeks --------------------------------------------------------------
    op.add_column("weeks", sa.Column("track_id", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE weeks SET track_id = phases.track_id "
        "FROM phases WHERE weeks.phase_id = phases.id"
    )
    op.alter_column("weeks", "track_id", nullable=False)
    op.create_foreign_key(
        "fk_weeks_track_id", "weeks", "tracks", ["track_id"], ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_weeks_track_id", "weeks", ["track_id"])

    # The globally unique week number is the hard blocker this migration exists
    # for. The plain index is recreated because the roadmap orders by it.
    op.drop_index("ix_weeks_number", table_name="weeks")
    op.create_index("ix_weeks_number", "weeks", ["number"])
    op.create_unique_constraint("uq_weeks_track_number", "weeks", ["track_id", "number"])


def downgrade() -> None:
    op.drop_constraint("uq_weeks_track_number", "weeks", type_="unique")
    op.drop_index("ix_weeks_number", table_name="weeks")
    op.create_index("ix_weeks_number", "weeks", ["number"], unique=True)
    op.drop_index("ix_weeks_track_id", table_name="weeks")
    op.drop_constraint("fk_weeks_track_id", "weeks", type_="foreignkey")
    op.drop_column("weeks", "track_id")

    op.drop_constraint("uq_phases_track_slug", "phases", type_="unique")
    op.drop_index("ix_phases_slug", table_name="phases")
    op.create_index("ix_phases_slug", "phases", ["slug"], unique=True)
    op.drop_index("ix_phases_track_id", table_name="phases")
    op.drop_constraint("fk_phases_track_id", "phases", type_="foreignkey")
    op.drop_column("phases", "track_id")

    op.drop_index("ix_tracks_is_certificate", table_name="tracks")
    op.drop_index("ix_tracks_is_topic", table_name="tracks")
    op.drop_index("ix_tracks_order_index", table_name="tracks")
    op.drop_index("ix_tracks_slug", table_name="tracks")
    op.drop_table("tracks")
