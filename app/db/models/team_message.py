from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class TeamMessage(Base):
    """Group chat for team members (creator included — creators are members)."""

    __tablename__ = "team_messages"
    __table_args__ = (
        Index("ix_team_messages_project_created", "team_project_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    team_project_id: Mapped[int] = mapped_column(
        ForeignKey("team_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Snapshot so history survives renames/deletions.
    sender_username: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    body: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    team_project: Mapped["TeamProject"] = relationship()
    sender: Mapped["User | None"] = relationship()


class ApplicationMessage(Base):
    """Private thread between an applicant and the team creator."""

    __tablename__ = "application_messages"
    __table_args__ = (
        Index(
            "ix_application_messages_app_created",
            "application_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    team_project_id: Mapped[int] = mapped_column(
        ForeignKey("team_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    application_id: Mapped[int] = mapped_column(
        ForeignKey("team_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    sender_username: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    body: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    application: Mapped["TeamApplication"] = relationship()
    sender: Mapped["User | None"] = relationship()
