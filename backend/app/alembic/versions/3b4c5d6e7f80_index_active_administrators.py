"""Index active administrator lookups.

Revision ID: 3b4c5d6e7f80
Revises: 2f3a4b5c6d7e
Create Date: 2026-08-16 22:00:00.000000
"""

from alembic import op

revision = "3b4c5d6e7f80"
down_revision = "2f3a4b5c6d7e"
branch_labels = None
depends_on = None

INDEX_NAME = "ix_user_role_is_active"


def upgrade() -> None:
    op.create_index(INDEX_NAME, "user", ["role", "is_active"], unique=False)


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="user")
