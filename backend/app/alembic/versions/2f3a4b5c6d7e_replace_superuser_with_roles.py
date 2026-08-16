"""Replace the binary administrator flag with roles.

Revision ID: 2f3a4b5c6d7e
Revises: fe56fa70289e
Create Date: 2026-08-16 21:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "2f3a4b5c6d7e"
down_revision = "fe56fa70289e"
branch_labels = None
depends_on = None

ROLE_CONSTRAINT = "ck_user_role"


def upgrade() -> None:
    op.add_column("user", sa.Column("role", sa.String(length=20), nullable=True))
    op.add_column(
        "user",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.execute(
        sa.text(
            'UPDATE "user" SET role = CASE '
            "WHEN is_superuser THEN 'admin' ELSE 'member' END"
        )
    )
    op.alter_column(
        "user",
        "role",
        existing_type=sa.String(length=20),
        nullable=False,
        server_default="member",
    )
    op.create_check_constraint(
        ROLE_CONSTRAINT,
        "user",
        "role IN ('admin', 'manager', 'member')",
    )
    op.drop_column("user", "is_superuser")


def downgrade() -> None:
    op.add_column(
        "user",
        sa.Column(
            "is_superuser",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.execute(sa.text("UPDATE \"user\" SET is_superuser = (role = 'admin')"))
    op.drop_constraint(ROLE_CONSTRAINT, "user", type_="check")
    op.drop_column("user", "must_change_password")
    op.drop_column("user", "role")
