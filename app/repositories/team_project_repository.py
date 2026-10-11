from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.models.team_message import ApplicationMessage, TeamMessage
from app.db.models.team_poll import TeamPoll, TeamPollOption, TeamPollVote
from app.db.models.team_project import (
    TeamApplication,
    TeamInvitation,
    TeamMembership,
    TeamProject,
    TeamProjectSkill,
    TeamRequestStatus,
)
from app.db.models.user import User


class TeamProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, project: TeamProject) -> TeamProject:
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_by_id(self, project_id: int) -> TeamProject | None:
        return (
            self.db.query(TeamProject)
            .filter(TeamProject.id == project_id)
            .first()
        )

    def get_by_id_with_relations(self, project_id: int) -> TeamProject | None:
        return (
            self.db.query(TeamProject)
            .options(
                selectinload(TeamProject.required_skills).selectinload(
                    TeamProjectSkill.skill
                ),
                selectinload(TeamProject.memberships).selectinload(
                    TeamMembership.user
                ),
            )
            .filter(TeamProject.id == project_id)
            .first()
        )

    def list_projects(
        self,
        skip: int = 0,
        limit: int = 20,
        college: str | None = None,
        q: str | None = None,
        kind: str | None = None,
        category: str | None = None,
        location: str | None = None,
        work_mode: str | None = None,
        hackathon: str | None = None,
    ) -> list[TeamProject]:
        query = self.db.query(TeamProject).order_by(TeamProject.created_at.desc())
        query = self._apply_discover_filters(
            query, college, q, kind, category, location, work_mode, hackathon
        )
        return query.offset(skip).limit(limit).all()

    def list_projects_filtered(
        self,
        college: str | None = None,
        q: str | None = None,
        kind: str | None = None,
        category: str | None = None,
        location: str | None = None,
        work_mode: str | None = None,
        hackathon: str | None = None,
        cap: int = 500,
    ) -> list[TeamProject]:
        """Unpaginated candidate set for Python-side tech/sort filtering."""
        query = self.db.query(TeamProject).order_by(TeamProject.created_at.desc())
        query = self._apply_discover_filters(
            query, college, q, kind, category, location, work_mode, hackathon
        )
        return query.limit(cap).all()

    @staticmethod
    def _apply_discover_filters(
        query, college, q, kind, category, location, work_mode, hackathon
    ):
        if college and college.strip():
            query = query.filter(TeamProject.college.ilike(college.strip()))
        if q and q.strip():
            escaped = (
                q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            )
            like = f"%{escaped}%"
            query = query.filter(
                (TeamProject.title.ilike(like, escape="\\"))
                | (TeamProject.description.ilike(like, escape="\\"))
            )
        if kind and kind.strip():
            query = query.filter(TeamProject.kind == kind.strip().lower())
        if category and category.strip():
            query = query.filter(TeamProject.category.ilike(category.strip()))
        if location and location.strip():
            escaped = (
                location.strip()
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            query = query.filter(
                TeamProject.location.ilike(f"%{escaped}%", escape="\\")
            )
        if work_mode and work_mode.strip():
            query = query.filter(TeamProject.work_mode == work_mode.strip().lower())
        if hackathon and hackathon.strip():
            escaped = (
                hackathon.strip()
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            query = query.filter(
                TeamProject.hackathon_name.ilike(f"%{escaped}%", escape="\\")
            )
        return query

    def count_projects(
        self,
        college: str | None = None,
        q: str | None = None,
        kind: str | None = None,
        category: str | None = None,
        location: str | None = None,
        work_mode: str | None = None,
        hackathon: str | None = None,
    ) -> int:
        query = self.db.query(TeamProject)
        query = self._apply_discover_filters(
            query, college, q, kind, category, location, work_mode, hackathon
        )
        return query.count()

    def update(self, project: TeamProject, data: dict) -> TeamProject:
        for key, value in data.items():
            setattr(project, key, value)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project: TeamProject) -> None:
        self.db.delete(project)
        self.db.commit()

    def add_required_skill(self, team_project_id: int, skill_id: int) -> TeamProjectSkill:
        link = TeamProjectSkill(team_project_id=team_project_id, skill_id=skill_id)
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def remove_required_skill(self, team_project_id: int, skill_id: int) -> bool:
        link = (
            self.db.query(TeamProjectSkill)
            .filter(
                TeamProjectSkill.team_project_id == team_project_id,
                TeamProjectSkill.skill_id == skill_id,
            )
            .first()
        )
        if link is None:
            return False
        self.db.delete(link)
        self.db.commit()
        return True

    def get_required_skills(self, team_project_id: int) -> list[TeamProjectSkill]:
        return (
            self.db.query(TeamProjectSkill)
            .options(joinedload(TeamProjectSkill.skill))
            .filter(TeamProjectSkill.team_project_id == team_project_id)
            .all()
        )

    def add_member(
        self, team_project_id: int, user_id: int, role: str = "member"
    ) -> TeamMembership:
        membership = TeamMembership(
            team_project_id=team_project_id, user_id=user_id, role=role
        )
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def get_membership(self, team_project_id: int, user_id: int) -> TeamMembership | None:
        return (
            self.db.query(TeamMembership)
            .filter(
                TeamMembership.team_project_id == team_project_id,
                TeamMembership.user_id == user_id,
            )
            .first()
        )

    def list_members(self, team_project_id: int) -> list[TeamMembership]:
        return (
            self.db.query(TeamMembership)
            .options(joinedload(TeamMembership.user).joinedload(User.profile))
            .filter(TeamMembership.team_project_id == team_project_id)
            .order_by(TeamMembership.joined_at)
            .all()
        )

    def count_members(self, team_project_id: int) -> int:
        return (
            self.db.query(TeamMembership)
            .filter(TeamMembership.team_project_id == team_project_id)
            .count()
        )

    def remove_member(self, membership: TeamMembership) -> None:
        self.db.delete(membership)
        self.db.commit()

    def list_member_project_ids(self, user_id: int) -> list[int]:
        rows = (
            self.db.query(TeamMembership.team_project_id)
            .filter(TeamMembership.user_id == user_id)
            .all()
        )
        return [row[0] for row in rows]

    def get_application(
        self, team_project_id: int, user_id: int
    ) -> TeamApplication | None:
        return (
            self.db.query(TeamApplication)
            .filter(
                TeamApplication.team_project_id == team_project_id,
                TeamApplication.user_id == user_id,
            )
            .first()
        )

    def get_application_by_id(self, application_id: int) -> TeamApplication | None:
        return (
            self.db.query(TeamApplication)
            .filter(TeamApplication.id == application_id)
            .first()
        )

    def create_application(
        self, team_project_id: int, user_id: int, message: str | None
    ) -> TeamApplication:
        application = TeamApplication(
            team_project_id=team_project_id,
            user_id=user_id,
            message=message,
            status=TeamRequestStatus.PENDING,
        )
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application

    def set_application_status(
        self, application: TeamApplication, status: TeamRequestStatus
    ) -> TeamApplication:
        application.status = status
        self.db.commit()
        self.db.refresh(application)
        return application

    def reset_application(
        self, application: TeamApplication, message: str | None
    ) -> TeamApplication:
        application.status = TeamRequestStatus.PENDING
        application.message = message
        self.db.commit()
        self.db.refresh(application)
        return application

    def list_applications(
        self, team_project_id: int, status: TeamRequestStatus | None = None
    ) -> list[TeamApplication]:
        query = (
            self.db.query(TeamApplication)
            .options(joinedload(TeamApplication.user).joinedload(User.profile))
            .filter(TeamApplication.team_project_id == team_project_id)
            .order_by(TeamApplication.created_at.desc())
        )
        if status is not None:
            query = query.filter(TeamApplication.status == status)
        return query.all()

    def list_user_applications(self, user_id: int) -> list[TeamApplication]:
        return (
            self.db.query(TeamApplication)
            .options(joinedload(TeamApplication.team_project))
            .filter(TeamApplication.user_id == user_id)
            .order_by(TeamApplication.created_at.desc())
            .all()
        )

    def get_invitation(
        self, team_project_id: int, invitee_id: int
    ) -> TeamInvitation | None:
        return (
            self.db.query(TeamInvitation)
            .filter(
                TeamInvitation.team_project_id == team_project_id,
                TeamInvitation.invitee_id == invitee_id,
            )
            .first()
        )

    def get_invitation_by_id(self, invitation_id: int) -> TeamInvitation | None:
        return (
            self.db.query(TeamInvitation)
            .filter(TeamInvitation.id == invitation_id)
            .first()
        )

    def create_invitation(
        self,
        team_project_id: int,
        inviter_id: int,
        invitee_id: int,
        message: str | None,
    ) -> TeamInvitation:
        invitation = TeamInvitation(
            team_project_id=team_project_id,
            inviter_id=inviter_id,
            invitee_id=invitee_id,
            message=message,
            status=TeamRequestStatus.PENDING,
        )
        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)
        return invitation

    def set_invitation_status(
        self, invitation: TeamInvitation, status: TeamRequestStatus
    ) -> TeamInvitation:
        invitation.status = status
        self.db.commit()
        self.db.refresh(invitation)
        return invitation

    def reset_invitation(
        self, invitation: TeamInvitation, message: str | None
    ) -> TeamInvitation:
        invitation.status = TeamRequestStatus.PENDING
        invitation.message = message
        self.db.commit()
        self.db.refresh(invitation)
        return invitation

    def list_user_invitations(self, invitee_id: int) -> list[TeamInvitation]:
        return (
            self.db.query(TeamInvitation)
            .options(joinedload(TeamInvitation.team_project))
            .filter(TeamInvitation.invitee_id == invitee_id)
            .order_by(TeamInvitation.created_at.desc())
            .all()
        )

    def application_status_map(self, team_project_id: int) -> dict[int, TeamRequestStatus]:
        rows = (
            self.db.query(TeamApplication.user_id, TeamApplication.status)
            .filter(TeamApplication.team_project_id == team_project_id)
            .all()
        )
        return {user_id: status for user_id, status in rows}

    def invitation_status_map(self, team_project_id: int) -> dict[int, TeamRequestStatus]:
        rows = (
            self.db.query(TeamInvitation.invitee_id, TeamInvitation.status)
            .filter(TeamInvitation.team_project_id == team_project_id)
            .all()
        )
        return {invitee_id: status for invitee_id, status in rows}

    # -- chat --------------------------------------------------------

    def create_team_message(
        self, team_project_id: int, sender_id: int | None, sender_username: str, body: str
    ) -> TeamMessage:
        message = TeamMessage(
            team_project_id=team_project_id,
            sender_id=sender_id,
            sender_username=sender_username,
            body=body,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def list_team_messages(
        self, team_project_id: int, limit: int = 50, before_id: int | None = None
    ) -> list[TeamMessage]:
        # Latest window by default (ascending for display); keyset page
        # older history with before_id.
        query = self.db.query(TeamMessage).filter(
            TeamMessage.team_project_id == team_project_id
        )
        if before_id is not None:
            query = query.filter(TeamMessage.id < before_id)
        rows = query.order_by(TeamMessage.id.desc()).limit(limit).all()
        return list(reversed(rows))

    def count_team_messages(self, team_project_id: int) -> int:
        return (
            self.db.query(TeamMessage)
            .filter(TeamMessage.team_project_id == team_project_id)
            .count()
        )

    def create_application_message(
        self,
        team_project_id: int,
        application_id: int,
        sender_id: int | None,
        sender_username: str,
        body: str,
    ) -> ApplicationMessage:
        message = ApplicationMessage(
            team_project_id=team_project_id,
            application_id=application_id,
            sender_id=sender_id,
            sender_username=sender_username,
            body=body,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def list_application_messages(
        self, application_id: int, limit: int = 50, before_id: int | None = None
    ) -> list[ApplicationMessage]:
        query = self.db.query(ApplicationMessage).filter(
            ApplicationMessage.application_id == application_id
        )
        if before_id is not None:
            query = query.filter(ApplicationMessage.id < before_id)
        rows = query.order_by(ApplicationMessage.id.desc()).limit(limit).all()
        return list(reversed(rows))

    # -- polls -------------------------------------------------------

    def create_poll(
        self,
        team_project_id: int,
        creator_id: int | None,
        creator_username: str,
        question: str,
        options: list[str],
        allow_multiple: bool = False,
    ) -> TeamPoll:
        poll = TeamPoll(
            team_project_id=team_project_id,
            creator_id=creator_id,
            creator_username=creator_username,
            question=question,
            is_closed=False,
            allow_multiple=allow_multiple,
        )
        self.db.add(poll)
        self.db.flush()
        for position, text in enumerate(options):
            self.db.add(
                TeamPollOption(poll_id=poll.id, text=text, position=position)
            )
        self.db.commit()
        self.db.refresh(poll)
        return poll

    def list_polls(self, team_project_id: int) -> list[TeamPoll]:
        return (
            self.db.query(TeamPoll)
            .options(selectinload(TeamPoll.options))
            .filter(TeamPoll.team_project_id == team_project_id)
            .order_by(TeamPoll.created_at.desc())
            .all()
        )

    def get_poll(self, poll_id: int) -> TeamPoll | None:
        return (
            self.db.query(TeamPoll)
            .options(selectinload(TeamPoll.options))
            .filter(TeamPoll.id == poll_id)
            .first()
        )

    def vote_counts(self, poll_id: int) -> dict[int, int]:
        from sqlalchemy import func as sa_func

        rows = (
            self.db.query(TeamPollVote.option_id, sa_func.count(TeamPollVote.id))
            .filter(TeamPollVote.poll_id == poll_id)
            .group_by(TeamPollVote.option_id)
            .all()
        )
        return {option_id: count for option_id, count in rows}

    def voter_option(self, poll_id: int, voter_id: int) -> int | None:
        row = (
            self.db.query(TeamPollVote.option_id)
            .filter(
                TeamPollVote.poll_id == poll_id,
                TeamPollVote.voter_id == voter_id,
            )
            .first()
        )
        return row[0] if row else None

    def voter_options(self, poll_id: int, voter_id: int) -> list[int]:
        rows = (
            self.db.query(TeamPollVote.option_id)
            .filter(
                TeamPollVote.poll_id == poll_id,
                TeamPollVote.voter_id == voter_id,
            )
            .all()
        )
        return [row[0] for row in rows]

    def remove_vote(self, poll_id: int, option_id: int, voter_id: int) -> None:
        self.db.query(TeamPollVote).filter(
            TeamPollVote.poll_id == poll_id,
            TeamPollVote.option_id == option_id,
            TeamPollVote.voter_id == voter_id,
        ).delete()
        self.db.flush()

    def cast_vote(self, poll_id: int, option_id: int, voter_id: int) -> None:
        # Single insert (flushed, not committed — the service commits once).
        # Concurrent duplicates hit the unique index; callers treat that as
        # idempotent success.
        exists = (
            self.db.query(TeamPollVote)
            .filter(
                TeamPollVote.poll_id == poll_id,
                TeamPollVote.option_id == option_id,
                TeamPollVote.voter_id == voter_id,
            )
            .first()
        )
        if exists is not None:
            return
        self.db.add(
            TeamPollVote(poll_id=poll_id, option_id=option_id, voter_id=voter_id)
        )
        self.db.flush()

    def clear_votes(self, poll_id: int, voter_id: int) -> None:
        self.db.query(TeamPollVote).filter(
            TeamPollVote.poll_id == poll_id,
            TeamPollVote.voter_id == voter_id,
        ).delete()
        self.db.flush()

    def close_poll(self, poll: TeamPoll) -> TeamPoll:
        poll.is_closed = True
        self.db.commit()
        self.db.refresh(poll)
        return poll
