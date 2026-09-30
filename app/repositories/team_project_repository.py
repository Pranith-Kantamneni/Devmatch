from sqlalchemy.orm import Session, joinedload, selectinload

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
        self, skip: int = 0, limit: int = 20, college: str | None = None, q: str | None = None
    ) -> list[TeamProject]:
        query = self.db.query(TeamProject).order_by(TeamProject.created_at.desc())
        if college:
            query = query.filter(TeamProject.college.ilike(college))
        if q:
            like = f"%{q}%"
            query = query.filter(
                (TeamProject.title.ilike(like)) | (TeamProject.description.ilike(like))
            )
        return query.offset(skip).limit(limit).all()

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
