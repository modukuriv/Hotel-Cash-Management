"""Remove password_hash from users

Revision ID: b4b2a1e2c0a1
Revises: 71bb436251f6
Create Date: 2026-03-14
"""
from alembic import op
import sqlalchemy as sa

revision = "b4b2a1e2c0a1"
down_revision = "71bb436251f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("password_hash")


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("password_hash", sa.String(), nullable=True))
