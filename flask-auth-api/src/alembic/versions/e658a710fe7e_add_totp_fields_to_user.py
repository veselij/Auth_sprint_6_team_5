"""add totp fields to user

Revision ID: e658a710fe7e
Revises: e6bea572fd1f
Create Date: 2022-05-28 22:21:02.346965

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e658a710fe7e"
down_revision = "e6bea572fd1f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("users", sa.Column("totp_secret", sa.String(), nullable=True))
    op.add_column("users", sa.Column("totp_active", sa.Boolean(), nullable=False))
    op.add_column("users", sa.Column("totp_sync", sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users", "totp_sync")
    op.drop_column("users", "totp_active")
    op.drop_column("users", "totp_secret")
    # ### end Alembic commands ###
