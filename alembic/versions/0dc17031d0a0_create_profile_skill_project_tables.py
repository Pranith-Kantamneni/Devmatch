"""create profile, skill, and project tables

Revision ID: 0dc17031d0a0
Revises: c3113ac17d03
Create Date: 2026-09-29 05:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0dc17031d0a0'
down_revision: Union[str, Sequence[str], None] = 'c3113ac17d03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


experience_level_enum = sa.Enum(
    "student", "junior", "mid", "senior", "lead",
    name="experience_level_enum",
    native_enum=False,
)
skill_category_enum = sa.Enum(
    "language", "framework", "tool", "domain", "other",
    name="skill_category_enum",
    native_enum=False,
)


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.add_column(
        'users',
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'developer_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('education', sa.String(length=255), nullable=True),
        sa.Column('experience_level', experience_level_enum, nullable=True),
        sa.Column('github_url', sa.String(length=255), nullable=True),
        sa.Column('linkedin_url', sa.String(length=255), nullable=True),
        sa.Column('portfolio_url', sa.String(length=255), nullable=True),
        sa.Column('availability', sa.Boolean(), nullable=False),
        sa.Column('collaboration_preferences', sa.Text(), nullable=True),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('embedding_updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(
        'ix_developer_profiles_user_id', 'developer_profiles', ['user_id'], unique=True
    )

    op.create_table(
        'skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', skill_category_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_skills_name', 'skills', ['name'], unique=True)

    op.create_table(
        'user_skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('proficiency', sa.Integer(), nullable=False),
        sa.Column('years_experience', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'skill_id', name='uq_user_skills_user_skill'),
    )
    op.create_index('ix_user_skills_user_id', 'user_skills', ['user_id'])
    op.create_index('ix_user_skills_skill_id', 'user_skills', ['skill_id'])

    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_projects_user_id', 'projects', ['user_id'])

    op.create_table(
        'project_skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'skill_id', name='uq_project_skills_project_skill'),
    )
    op.create_index('ix_project_skills_project_id', 'project_skills', ['project_id'])
    op.create_index('ix_project_skills_skill_id', 'project_skills', ['skill_id'])

    op.drop_column('users', 'full_name')
    op.drop_column('users', 'bio')
    op.drop_column('users', 'experience_level')
    op.drop_column('users', 'github_url')
    op.drop_column('users', 'linkedin_url')


def downgrade() -> None:
    op.add_column('users', sa.Column('linkedin_url', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('github_url', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('experience_level', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('full_name', sa.String(length=100), nullable=True))

    op.drop_index('ix_project_skills_skill_id', table_name='project_skills')
    op.drop_index('ix_project_skills_project_id', table_name='project_skills')
    op.drop_table('project_skills')
    op.drop_index('ix_projects_user_id', table_name='projects')
    op.drop_table('projects')
    op.drop_index('ix_user_skills_skill_id', table_name='user_skills')
    op.drop_index('ix_user_skills_user_id', table_name='user_skills')
    op.drop_table('user_skills')
    op.drop_index('ix_skills_name', table_name='skills')
    op.drop_table('skills')
    op.drop_index('ix_developer_profiles_user_id', table_name='developer_profiles')
    op.drop_table('developer_profiles')

    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'created_at')
