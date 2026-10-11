"""add dm conversations/messages and team polls

Revision ID: 5c9f3a7e4d66
Revises: 4b8e1d2f3c55
Create Date: 2026-10-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c9f3a7e4d66'
down_revision: Union[str, Sequence[str], None] = '4b8e1d2f3c55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'direct_conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('requester_id', sa.Integer(), nullable=False),
        sa.Column('addressee_id', sa.Integer(), nullable=False),
        sa.Column('pair_key', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['addressee_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pair_key'),
    )
    op.create_index('ix_direct_conversations_requester_id', 'direct_conversations', ['requester_id'])
    op.create_index('ix_direct_conversations_addressee_id', 'direct_conversations', ['addressee_id'])

    op.create_table(
        'direct_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=True),
        sa.Column('sender_username', sa.String(length=50), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['direct_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_direct_messages_conversation_id', 'direct_messages', ['conversation_id'])
    op.create_index(
        'ix_direct_messages_convo_created',
        'direct_messages',
        ['conversation_id', 'created_at'],
    )

    op.create_table(
        'team_polls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_project_id', sa.Integer(), nullable=False),
        sa.Column('creator_id', sa.Integer(), nullable=True),
        sa.Column('creator_username', sa.String(length=50), nullable=False),
        sa.Column('question', sa.String(length=280), nullable=False),
        sa.Column('is_closed', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['team_project_id'], ['team_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_team_polls_team_project_id', 'team_polls', ['team_project_id'])

    op.create_table(
        'team_poll_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('poll_id', sa.Integer(), nullable=False),
        sa.Column('text', sa.String(length=120), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['poll_id'], ['team_polls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_team_poll_options_poll_id', 'team_poll_options', ['poll_id'])

    op.create_table(
        'team_poll_votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('poll_id', sa.Integer(), nullable=False),
        sa.Column('option_id', sa.Integer(), nullable=False),
        sa.Column('voter_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['poll_id'], ['team_polls.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['option_id'], ['team_poll_options.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['voter_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_team_poll_votes_poll_id', 'team_poll_votes', ['poll_id'])
    op.create_index('ix_team_poll_votes_voter_id', 'team_poll_votes', ['voter_id'])
    op.create_index('uq_poll_votes_poll_voter', 'team_poll_votes', ['poll_id', 'voter_id'], unique=True)


def downgrade() -> None:
    op.drop_index('uq_poll_votes_poll_voter', table_name='team_poll_votes')
    op.drop_index('ix_team_poll_votes_voter_id', table_name='team_poll_votes')
    op.drop_index('ix_team_poll_votes_poll_id', table_name='team_poll_votes')
    op.drop_table('team_poll_votes')
    op.drop_index('ix_team_poll_options_poll_id', table_name='team_poll_options')
    op.drop_table('team_poll_options')
    op.drop_index('ix_team_polls_team_project_id', table_name='team_polls')
    op.drop_table('team_polls')
    op.drop_index('ix_direct_messages_convo_created', table_name='direct_messages')
    op.drop_index('ix_direct_messages_conversation_id', table_name='direct_messages')
    op.drop_table('direct_messages')
    op.drop_index('ix_direct_conversations_addressee_id', table_name='direct_conversations')
    op.drop_index('ix_direct_conversations_requester_id', table_name='direct_conversations')
    op.drop_table('direct_conversations')
