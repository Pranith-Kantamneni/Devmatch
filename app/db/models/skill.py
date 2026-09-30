from datetime import datetime
from enum import Enum as PyEnum

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class SkillCategory(str, PyEnum):
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    TOOL = "tool"
    DOMAIN = "domain"
    OTHER = "other"


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        sa.String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    category: Mapped[SkillCategory] = mapped_column(
        sa.Enum(SkillCategory, name="skill_category_enum", native_enum=False),
        nullable=False,
        default=SkillCategory.OTHER,
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        server_default=sa.func.now(),
        nullable=False,
    )

    user_skills: Mapped[list["UserSkill"]] = relationship(
        back_populates="skill",
        cascade="all, delete-orphan",
    )

    project_skills: Mapped[list["ProjectSkill"]] = relationship(
        back_populates="skill",
        cascade="all, delete-orphan",
    )


class UserSkill(Base):
    __tablename__ = "user_skills"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    skill_id: Mapped[int] = mapped_column(
        sa.ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    proficiency: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=3,
    )

    years_experience: Mapped[float | None] = mapped_column(sa.Float)

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        server_default=sa.func.now(),
        nullable=False,
    )

    __table_args__ = (
        sa.UniqueConstraint("user_id", "skill_id", name="uq_user_skills_user_skill"),
    )

    user: Mapped["User"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship(back_populates="user_skills")
