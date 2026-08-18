"""every track starts separately

Adds `track_enrollments` and moves the exam date onto it.

`users.target_exam_date` was one column, so it could only ever describe one
exam. Somebody studying CKA and LFCS at the same time needs two dates, two start
days and two countdowns. The column is migrated into an enrollment for the
default track and then dropped; `downgrade()` puts it back.

**The backfill is the load-bearing part.** With ENFORCE_TRACK_START on, a user
with no enrollment cannot open any content. Every existing user has been
studying without one - so without this, the first deploy locks the whole
platform behind a Start button nobody was told about. Anyone with lesson
progress therefore gets an active enrollment for the track that progress belongs
to, backdated to when they actually started.

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-19 00:00:00

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Fallback when a track carries no week structure yet. Mirrors
# `TRACK_DEFAULT_WEEKS` in config.py - a track with no phases still needs a
# target date, or the countdown has nothing to count to.
DEFAULT_WEEKS = 20

# started_at is the earliest completion in that track, because that is when the
# person demonstrably began. Falling back to the account's creation date keeps
# the row honest for someone who enrolled but has completed nothing yet.
BACKFILL = f"""
INSERT INTO track_enrollments (
    user_id, track_id, started_at, auto_target_date, target_date,
    target_source, status, created_at, updated_at
)
SELECT
    s.user_id,
    s.track_id,
    s.started_at,
    (s.started_at::date + (s.weeks * 7)::int) AS auto_target_date,
    COALESCE(
        u.target_exam_date,
        s.started_at::date + (s.weeks * 7)::int
    ) AS target_date,
    CASE WHEN u.target_exam_date IS NOT NULL AND s.is_default
         THEN 'manual' ELSE 'auto' END AS target_source,
    'active',
    now(),
    now()
FROM (
    SELECT
        lp.user_id,
        w.track_id,
        COALESCE(MIN(lp.completed_at), MIN(us.created_at)) AS started_at,
        -- The TRACK's length, not the length of the phases this user happens
        -- to have touched. Joining phases into the aggregate would give a
        -- student who finished one week in phase 1 a four-week roadmap, and the
        -- date it produced would be wrong forever.
        COALESCE(
            NULLIF(
                (SELECT MAX(p2.week_end) FROM phases p2 WHERE p2.track_id = w.track_id),
                0
            ),
            (SELECT COUNT(*)::int FROM weeks w2 WHERE w2.track_id = w.track_id),
            {DEFAULT_WEEKS}
        ) AS weeks,
        (w.track_id = (SELECT id FROM tracks ORDER BY order_index, id LIMIT 1))
            AS is_default
    FROM lesson_progress lp
    JOIN lessons l ON l.id = lp.lesson_id
    JOIN weeks w ON w.id = l.week_id
    JOIN users us ON us.id = lp.user_id
    GROUP BY lp.user_id, w.track_id
) AS s
JOIN users u ON u.id = s.user_id
ON CONFLICT (user_id, track_id) DO NOTHING
"""

# A user who set an exam date but never completed a lesson still gets an
# enrollment, otherwise the date they chose is simply lost.
BACKFILL_DATE_ONLY = f"""
INSERT INTO track_enrollments (
    user_id, track_id, started_at, auto_target_date, target_date,
    target_source, status, created_at, updated_at
)
SELECT
    u.id,
    (SELECT id FROM tracks ORDER BY order_index, id LIMIT 1),
    u.created_at,
    (u.created_at::date + ({DEFAULT_WEEKS} * 7)),
    u.target_exam_date,
    'manual',
    'active',
    now(),
    now()
FROM users u
WHERE u.target_exam_date IS NOT NULL
  AND EXISTS (SELECT 1 FROM tracks)
ON CONFLICT (user_id, track_id) DO NOTHING
"""


def upgrade() -> None:
    op.create_table(
        "track_enrollments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("auto_target_date", sa.Date(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("target_source", sa.String(length=10), nullable=False,
                  server_default="auto"),
        sa.Column("status", sa.String(length=20), nullable=False,
                  server_default="active"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "track_id", name="uq_enrollment_user_track"),
    )
    op.create_index("ix_track_enrollments_user_id", "track_enrollments", ["user_id"])
    op.create_index("ix_track_enrollments_track_id", "track_enrollments", ["track_id"])
    op.create_index("ix_track_enrollments_status", "track_enrollments", ["status"])

    # Order matters: the progress-based backfill runs first so that a user who
    # has both progress and a chosen date gets one row carrying the date, rather
    # than two rows or a lost date. The second pass only fills what the first
    # left, via ON CONFLICT DO NOTHING.
    op.execute(BACKFILL)
    op.execute(BACKFILL_DATE_ONLY)

    op.drop_column("users", "target_exam_date")


def downgrade() -> None:
    op.add_column("users", sa.Column("target_exam_date", sa.Date(), nullable=True))
    # Restore what the column can hold: one date, from the default track.
    op.execute(
        """
        UPDATE users u
        SET target_exam_date = e.target_date
        FROM track_enrollments e
        WHERE e.user_id = u.id
          AND e.track_id = (SELECT id FROM tracks ORDER BY order_index, id LIMIT 1)
        """
    )
    op.drop_index("ix_track_enrollments_status", table_name="track_enrollments")
    op.drop_index("ix_track_enrollments_track_id", table_name="track_enrollments")
    op.drop_index("ix_track_enrollments_user_id", table_name="track_enrollments")
    op.drop_table("track_enrollments")
