"""add learning path tracking to user

Revision ID: add_learning_path_tracking_to_user
Revises: add_google_oauth_fields_to_user_model
Create Date: 2023-11-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_learning_path_tracking_to_user'
down_revision = 'add_google_oauth_fields_to_user_model'
branch_labels = None
depends_on = None


def upgrade():
    # Add learning path tracking columns to user table
    op.add_column('users', sa.Column('current_plan_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('current_month_index', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('current_day', sa.Integer(), nullable=True))


def downgrade():
    # Remove learning path tracking columns from user table
    op.drop_column('users', 'current_day')
    op.drop_column('users', 'current_month_index')
    op.drop_column('users', 'current_plan_id')