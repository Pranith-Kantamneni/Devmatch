from datetime import datetime
from enum import Enum as PyEnum

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class ExperienceLevel(str, PyEnum):
    STUDENT = "student"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"


class DeveloperProfile(Base):
    __tablename__ = "developer_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    full_name: Mapped[str | None] = mapped_column(sa.String(100))

    bio: Mapped[str | None] = mapped_column(sa.Text)

    location: Mapped[str | None] = mapped_column(sa.String(100))

    education: Mapped[str | None] = mapped_column(sa.String(255))

    college: Mapped[str | None] = mapped_column(sa.String(255))

    experience_level: Mapped[ExperienceLevel | None] = mapped_column(
        sa.Enum(ExperienceLevel, name="experience_level_enum", native_enum=False),
    )

    github_url: Mapped[str | None] = mapped_column(sa.String(255))

    linkedin_url: Mapped[str | None] = mapped_column(sa.String(255))

    portfolio_url: Mapped[str | None] = mapped_column(sa.String(255))

    availability: Mapped[bool] = mapped_column(default=True, nullable=False)

    collaboration_preferences: Mapped[str | None] = mapped_column(sa.Text)

    embedding: Mapped[list[float] | None] = mapped_column(sa.JSON)

    embedding_updated_at: Mapped[datetime | None] = mapped_column(sa.DateTime)

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        server_default=sa.func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="profile")
