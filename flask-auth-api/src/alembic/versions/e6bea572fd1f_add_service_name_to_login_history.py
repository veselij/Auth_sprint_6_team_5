"""add service_name to login history

Revision ID: e6bea572fd1f
Revises: 352bbeb9587c
Create Date: 2022-05-26 23:02:20.038170

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e6bea572fd1f"
down_revision = "352bbeb9587c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("users_access_history", sa.Column("service_name", sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users_access_history", "service_name")
    # ### end Alembic commands ###