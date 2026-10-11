from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class TeamPoll(Base):
    __tablename__ = "team_polls"

    id: Mapped[int] = mapped_column(primary_key=True)

    team_project_id: Mapped[int] = mapped_column(
        ForeignKey("team_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    creator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    creator_username: Mapped[str] = mapped_column(
        String(50), nullable=False, default=""
    )

    question: Mapped[str] = mapped_column(String(280), nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    team_project: Mapped["TeamProject"] = relationship()
    options: Mapped[list["TeamPollOption"]] = relationship(
        back_populates="poll", cascade="all, delete-orphan"
    )


class TeamPollOption(Base):
    __tablename__ = "team_poll_options"

    id: Mapped[int] = mapped_column(primary_key=True)

    poll_id: Mapped[int] = mapped_column(
        ForeignKey("team_polls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(String(120), nullable=False)
    position: Mapped[int] = mapped_column(nullable=False, default=0)

    poll: Mapped["TeamPoll"] = relationship(back_populates="options")


class TeamPollVote(Base):
    __tablename__ = "team_poll_votes"
    __table_args__ = (
        Index("uq_poll_votes_poll_voter", "poll_id", "voter_id", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    poll_id: Mapped[int] = mapped_column(
        ForeignKey("team_polls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    option_id: Mapped[int] = mapped_column(
        ForeignKey("team_poll_options.id", ondelete="CASCADE"), nullable=False
    )
    voter_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
