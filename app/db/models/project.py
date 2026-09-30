from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(sa.String(200), nullable=False)

    description: Mapped[str | None] = mapped_column(sa.Text)

    url: Mapped[str | None] = mapped_column(sa.String(255))

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        server_default=sa.func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="projects")
    skills: Mapped[list["ProjectSkill"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class ProjectSkill(Base):
    __tablename__ = "project_skills"

    id: Mapped[int] = mapped_column(primary_key=True)

    project_id: Mapped[int] = mapped_column(
        sa.ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    skill_id: Mapped[int] = mapped_column(
        sa.ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "project_id", "skill_id", name="uq_project_skills_project_skill"
        ),
    )

    project: Mapped["Project"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship(back_populates="project_skills")
