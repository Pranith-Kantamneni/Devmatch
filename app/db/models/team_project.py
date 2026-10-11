from datetime import datetime
from enum import Enum as PyEnum

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class TeamRequestStatus(str, PyEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TeamProject(Base):
    __tablename__ = "team_projects"

    id: Mapped[int] = mapped_column(primary_key=True)

    creator_id: Mapped[int] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(sa.String(200), nullable=False)

    description: Mapped[str | None] = mapped_column(sa.Text)

    tech_stack: Mapped[list[str] | None] = mapped_column(sa.JSON)

    poster_url: Mapped[str | None] = mapped_column(sa.String(500))

    max_members: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    college: Mapped[str | None] = mapped_column(sa.String(255))

    college_id: Mapped[str | None] = mapped_column(sa.String(100), index=True)

    require_same_college: Mapped[bool] = mapped_column(default=False, nullable=False)

    kind: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, default="project", server_default="project"
    )
    category: Mapped[str | None] = mapped_column(sa.String(60))
    hackathon_name: Mapped[str | None] = mapped_column(sa.String(200))
    location: Mapped[str | None] = mapped_column(sa.String(120))
    work_mode: Mapped[str | None] = mapped_column(sa.String(20))

    allow_member_polls: Mapped[bool] = mapped_column(
        default=True, nullable=False, server_default=sa.true()
    )
    allow_member_invites: Mapped[bool] = mapped_column(
        default=False, nullable=False, server_default=sa.false()
    )

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

    creator: Mapped["User"] = relationship()
    required_skills: Mapped[list["TeamProjectSkill"]] = relationship(
        back_populates="team_project",
        cascade="all, delete-orphan",
    )
    memberships: Mapped[list["TeamMembership"]] = relationship(
        back_populates="team_project",
        cascade="all, delete-orphan",
    )
    applications: Mapped[list["TeamApplication"]] = relationship(
        back_populates="team_project",
        cascade="all, delete-orphan",
    )
    invitations: Mapped[list["TeamInvitation"]] = relationship(
        back_populates="team_project",
        cascade="all, delete-orphan",
    )


class TeamProjectSkill(Base):
    __tablename__ = "team_project_skills"

    id: Mapped[int] = mapped_column(primary_key=True)

    team_project_id: Mapped[int] = mapped_column(
        sa.ForeignKey("team_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    skill_id: Mapped[int] = mapped_column(
        sa.ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        server_default=sa.func.now(),
        nullable=False,
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "team_project_id", "skill_id", name="uq_team_project_skills_project_skill"
        ),
    )

    team_project: Mapped["TeamProject"] = relationship(back_populates="required_skills")
    skill: Mapped["Skill"] = relationship()


class TeamMembership(Base):
    __tablename__ = "team_memberships"

    id: Mapped[int] = mapped_column(primary_key=True)

    team_project_id: Mapped[int] = mapped_column(
        sa.ForeignKey("team_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="member")

    joined_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        server_default=sa.func.now(),
        nullable=False,
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "team_project_id", "user_id", name="uq_team_memberships_project_user"
        ),
    )

    team_project: Mapped["TeamProject"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship()


class TeamApplication(Base):
    __tablename__ = "team_applications"

    id: Mapped[int] = mapped_column(primary_key=True)

    team_project_id: Mapped[int] = mapped_column(
        sa.ForeignKey("team_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    message: Mapped[str | None] = mapped_column(sa.Text)

    status: Mapped[TeamRequestStatus] = mapped_column(
        sa.Enum(TeamRequestStatus, name="team_request_status_enum", native_enum=False),
        nullable=False,
        default=TeamRequestStatus.PENDING,
    )

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

    __table_args__ = (
        sa.UniqueConstraint(
            "team_project_id", "user_id", name="uq_team_applications_project_user"
        ),
    )

    team_project: Mapped["TeamProject"] = relationship(back_populates="applications")
    user: Mapped["User"] = relationship()


class TeamInvitation(Base):
    __tablename__ = "team_invitations"

    id: Mapped[int] = mapped_column(primary_key=True)

    team_project_id: Mapped[int] = mapped_column(
        sa.ForeignKey("team_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    inviter_id: Mapped[int] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    invitee_id: Mapped[int] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    message: Mapped[str | None] = mapped_column(sa.Text)

    status: Mapped[TeamRequestStatus] = mapped_column(
        sa.Enum(TeamRequestStatus, name="team_request_status_enum", native_enum=False),
        nullable=False,
        default=TeamRequestStatus.PENDING,
    )

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

    __table_args__ = (
        sa.UniqueConstraint(
            "team_project_id", "invitee_id", name="uq_team_invitations_project_invitee"
        ),
    )

    team_project: Mapped["TeamProject"] = relationship(back_populates="invitations")
