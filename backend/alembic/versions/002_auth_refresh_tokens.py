"""Add refresh tokens and restrict user roles to admin/viewer."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_auth_refresh_tokens"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE users SET role = 'viewer' WHERE role = 'operator'")

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("jti", sa.String(length=36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jti"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)
    op.create_index("ix_refresh_tokens_jti", "refresh_tokens", ["jti"], unique=True)

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE user_role_enum RENAME TO user_role_enum_old")
        op.execute("CREATE TYPE user_role_enum AS ENUM ('admin', 'viewer')")
        op.execute(
            "ALTER TABLE users ALTER COLUMN role TYPE user_role_enum "
            "USING role::text::user_role_enum"
        )
        op.execute("DROP TYPE user_role_enum_old")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE user_role_enum RENAME TO user_role_enum_old")
        op.execute("CREATE TYPE user_role_enum AS ENUM ('admin', 'operator', 'viewer')")
        op.execute(
            "ALTER TABLE users ALTER COLUMN role TYPE user_role_enum "
            "USING role::text::user_role_enum"
        )
        op.execute("DROP TYPE user_role_enum_old")

    op.drop_index("ix_refresh_tokens_jti", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
