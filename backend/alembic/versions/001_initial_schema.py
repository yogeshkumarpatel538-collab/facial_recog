"""Initial schema for People Counting System."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cameras",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("rtsp_url", sa.String(length=512), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "viewer", name="user_role_enum"),
            nullable=False,
            server_default="viewer",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "count_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("camera_id", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.String(length=64), nullable=False),
        sa.Column(
            "direction",
            sa.Enum("in", "out", name="direction_enum"),
            nullable=False,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["camera_id"], ["cameras.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_count_events_camera_id", "count_events", ["camera_id"], unique=False)
    op.create_index("ix_count_events_timestamp", "count_events", ["timestamp"], unique=False)

    op.create_table(
        "daily_summaries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("camera_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("total_in", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_out", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["camera_id"], ["cameras.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("camera_id", "date", name="uq_daily_summary_camera_date"),
    )
    op.create_index("ix_daily_summaries_camera_id", "daily_summaries", ["camera_id"], unique=False)
    op.create_index("ix_daily_summaries_date", "daily_summaries", ["date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_daily_summaries_date", table_name="daily_summaries")
    op.drop_index("ix_daily_summaries_camera_id", table_name="daily_summaries")
    op.drop_table("daily_summaries")

    op.drop_index("ix_count_events_timestamp", table_name="count_events")
    op.drop_index("ix_count_events_camera_id", table_name="count_events")
    op.drop_table("count_events")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS user_role_enum")

    op.drop_table("cameras")
    op.execute("DROP TYPE IF EXISTS direction_enum")
