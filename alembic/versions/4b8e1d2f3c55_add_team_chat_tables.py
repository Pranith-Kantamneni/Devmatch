"""add team group chat and application message tables

Revision ID: 4b8e1d2f3c55
Revises: 3a7f2c9e1b44
Create Date: 2026-10-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b8e1d2f3c55'
down_revision: Union[str, Sequence[str], None] = '3a7f2c9e1b44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'team_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_project_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=True),
        sa.Column('sender_username', sa.String(length=50), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['team_project_id'], ['team_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_team_messages_team_project_id', 'team_messages', ['team_project_id'])
    op.create_index(
        'ix_team_messages_project_created',
        'team_messages',
        ['team_project_id', 'created_at'],
    )

    op.create_table(
        'application_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_project_id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=True),
        sa.Column('sender_username', sa.String(length=50), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['team_project_id'], ['team_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['application_id'], ['team_applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_application_messages_team_project_id', 'application_messages', ['team_project_id'])
    op.create_index('ix_application_messages_application_id', 'application_messages', ['application_id'])
    op.create_index(
        'ix_application_messages_app_created',
        'application_messages',
        ['application_id', 'created_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_application_messages_app_created', table_name='application_messages')
    op.drop_index('ix_application_messages_application_id', table_name='application_messages')
    op.drop_index('ix_application_messages_team_project_id', table_name='application_messages')
    op.drop_table('application_messages')
    op.drop_index('ix_team_messages_project_created', table_name='team_messages')
    op.drop_index('ix_team_messages_team_project_id', table_name='team_messages')
    op.drop_table('team_messages')
