"""create team project tables and add college to profiles

Revision ID: 2f50baebc369
Revises: 0dc17031d0a0
Create Date: 2026-09-29 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2f50baebc369'
down_revision: Union[str, Sequence[str], None] = '0dc17031d0a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


team_request_status_enum = sa.Enum(
    "pending", "accepted", "rejected",
    name="team_request_status_enum",
    native_enum=False,
)


def upgrade() -> None:
    op.add_column(
        'developer_profiles', sa.Column('college', sa.String(length=255), nullable=True)
    )

    op.create_table(
        'team_projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tech_stack', sa.JSON(), nullable=True),
        sa.Column('poster_url', sa.String(length=500), nullable=True),
        sa.Column('max_members', sa.Integer(), nullable=False),
        sa.Column('college', sa.String(length=255), nullable=True),
        sa.Column('require_same_college', sa.Boolean(), nullable=False),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('embedding_updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_team_projects_creator_id', 'team_projects', ['creator_id'])

    op.create_table(
        'team_project_skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_project_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['team_project_id'], ['team_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_project_id', 'skill_id', name='uq_team_project_skills_project_skill'),
    )
    op.create_index('ix_team_project_skills_team_project_id', 'team_project_skills', ['team_project_id'])
    op.create_index('ix_team_project_skills_skill_id', 'team_project_skills', ['skill_id'])

    op.create_table(
        'team_memberships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_project_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['team_project_id'], ['team_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_project_id', 'user_id', name='uq_team_memberships_project_user'),
    )
    op.create_index('ix_team_memberships_team_project_id', 'team_memberships', ['team_project_id'])
    op.create_index('ix_team_memberships_user_id', 'team_memberships', ['user_id'])

    op.create_table(
        'team_applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_project_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', team_request_status_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['team_project_id'], ['team_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_project_id', 'user_id', name='uq_team_applications_project_user'),
    )
    op.create_index('ix_team_applications_team_project_id', 'team_applications', ['team_project_id'])
    op.create_index('ix_team_applications_user_id', 'team_applications', ['user_id'])

    op.create_table(
        'team_invitations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_project_id', sa.Integer(), nullable=False),
        sa.Column('inviter_id', sa.Integer(), nullable=False),
        sa.Column('invitee_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', team_request_status_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['team_project_id'], ['team_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inviter_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invitee_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_project_id', 'invitee_id', name='uq_team_invitations_project_invitee'),
    )
    op.create_index('ix_team_invitations_team_project_id', 'team_invitations', ['team_project_id'])
    op.create_index('ix_team_invitations_invitee_id', 'team_invitations', ['invitee_id'])


def downgrade() -> None:
    op.drop_index('ix_team_invitations_invitee_id', table_name='team_invitations')
    op.drop_index('ix_team_invitations_team_project_id', table_name='team_invitations')
    op.drop_table('team_invitations')
    op.drop_index('ix_team_applications_user_id', table_name='team_applications')
    op.drop_index('ix_team_applications_team_project_id', table_name='team_applications')
    op.drop_table('team_applications')
    op.drop_index('ix_team_memberships_user_id', table_name='team_memberships')
    op.drop_index('ix_team_memberships_team_project_id', table_name='team_memberships')
    op.drop_table('team_memberships')
    op.drop_index('ix_team_project_skills_skill_id', table_name='team_project_skills')
    op.drop_index('ix_team_project_skills_team_project_id', table_name='team_project_skills')
    op.drop_table('team_project_skills')
    op.drop_index('ix_team_projects_creator_id', table_name='team_projects')
    op.drop_table('team_projects')

    op.drop_column('developer_profiles', 'college')
