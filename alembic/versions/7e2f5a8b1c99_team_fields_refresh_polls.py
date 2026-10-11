"""team discovery fields, refresh tokens, multi-choice polls

Revision ID: 7e2f5a8b1c99
Revises: 6d1e4b8f5c77
Create Date: 2026-10-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e2f5a8b1c99'
down_revision: Union[str, Sequence[str], None] = '6d1e4b8f5c77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('team_projects', sa.Column('kind', sa.String(length=20), server_default='project', nullable=False))
    op.add_column('team_projects', sa.Column('category', sa.String(length=60), nullable=True))
    op.add_column('team_projects', sa.Column('hackathon_name', sa.String(length=200), nullable=True))
    op.add_column('team_projects', sa.Column('location', sa.String(length=120), nullable=True))
    op.add_column('team_projects', sa.Column('work_mode', sa.String(length=20), nullable=True))
    op.add_column('team_projects', sa.Column('allow_member_polls', sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column('team_projects', sa.Column('allow_member_invites', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.create_index('ix_team_projects_kind', 'team_projects', ['kind'])

    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])

    op.add_column('team_polls', sa.Column('allow_multiple', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.drop_index('uq_poll_votes_poll_voter', table_name='team_poll_votes')
    op.create_index('uq_poll_votes_poll_option_voter', 'team_poll_votes', ['poll_id', 'option_id', 'voter_id'], unique=True)


def downgrade() -> None:
    op.drop_index('uq_poll_votes_poll_option_voter', table_name='team_poll_votes')
    op.create_index('uq_poll_votes_poll_voter', 'team_poll_votes', ['poll_id', 'voter_id'], unique=True)
    op.drop_column('team_polls', 'allow_multiple')
    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_index('ix_team_projects_kind', table_name='team_projects')
    op.drop_column('team_projects', 'allow_member_invites')
    op.drop_column('team_projects', 'allow_member_polls')
    op.drop_column('team_projects', 'location')
    op.drop_column('team_projects', 'work_mode')
    op.drop_column('team_projects', 'hackathon_name')
    op.drop_column('team_projects', 'category')
    op.drop_column('team_projects', 'kind')
