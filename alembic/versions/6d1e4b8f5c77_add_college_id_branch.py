"""add canonical college ids and profile branch

Revision ID: 6d1e4b8f5c77
Revises: 5c9f3a7e4d66
Create Date: 2026-10-10 00:00:00.000000

Backfills college_id by resolving existing free-text college values
against the canonical directory (best effort; unresolvable stays NULL
and matching falls back to text comparison).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d1e4b8f5c77'
down_revision: Union[str, Sequence[str], None] = '5c9f3a7e4d66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('developer_profiles', sa.Column('college_id', sa.String(length=100), nullable=True))
    op.add_column('developer_profiles', sa.Column('branch', sa.String(length=100), nullable=True))
    op.add_column('team_projects', sa.Column('college_id', sa.String(length=100), nullable=True))
    op.create_index('ix_developer_profiles_college_id', 'developer_profiles', ['college_id'])
    op.create_index('ix_team_projects_college_id', 'team_projects', ['college_id'])

    # Best-effort backfill of canonical ids from existing free text.
    try:
        from app.data.colleges import resolve_college

        connection = op.get_bind()
        for table in ("developer_profiles", "team_projects"):
            rows = connection.execute(
                sa.text(f"SELECT id, college FROM {table} WHERE college IS NOT NULL")
            ).fetchall()
            for row_id, college in rows:
                entry = resolve_college(college)
                if entry is not None:
                    connection.execute(
                        sa.text(f"UPDATE {table} SET college_id = :cid WHERE id = :rid"),
                        {"cid": entry["id"], "rid": row_id},
                    )
    except Exception:
        # Backfill is best-effort; NULL ids fall back to text comparison.
        pass


def downgrade() -> None:
    op.drop_index('ix_team_projects_college_id', table_name='team_projects')
    op.drop_index('ix_developer_profiles_college_id', table_name='developer_profiles')
    op.drop_column('team_projects', 'college_id')
    op.drop_column('developer_profiles', 'branch')
    op.drop_column('developer_profiles', 'college_id')
