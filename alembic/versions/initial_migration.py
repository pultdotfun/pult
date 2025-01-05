"""initial migration

Revision ID: 1234567890ab
Revises: 
Create Date: 2023-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '1234567890ab'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('twitter_id', sa.String(), nullable=True),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('access_token', sa.String(), nullable=True),
        sa.Column('refresh_token', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_processed', sa.DateTime(), nullable=True),
        sa.Column('engagement_data', sa.JSON(), nullable=True),
        sa.Column('pult_score', sa.Float(), nullable=True),
        sa.Column('is_enterprise', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('twitter_id')
    )

    op.create_table(
        'engagements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('tweet_id', sa.String(), nullable=True),
        sa.Column('engagement_type', sa.String(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('engagements')
    op.drop_table('users') 