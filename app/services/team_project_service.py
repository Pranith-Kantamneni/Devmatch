from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.db.models.team_project import TeamProject, TeamRequestStatus
from app.repositories.profile_repository import ProfileRepository
from app.repositories.skill_repository import SkillRepository
from app.repositories.team_project_repository import TeamProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.skill import SkillBrief
from app.schemas.team_project import (
    TeamApplicationResponse,
    TeamInvitationResponse,
    TeamMemberResponse,
    TeamProjectCreate,
    TeamProjectDetailResponse,
    TeamProjectResponse,
    TeamProjectUpdate,
)
from app.services.embedding_service import EmbeddingService


class TeamProjectService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        embedding_service: EmbeddingService,
    ):
        self.db = db
        self.settings = settings
        self.embedding_service = embedding_service
        self.team_repo = TeamProjectRepository(db)
        self.user_repo = UserRepository(db)
        self.skill_repo = SkillRepository(db)
        self.profile_repo = ProfileRepository(db)

    def create_project(self, creator_id: int, data: TeamProjectCreate) -> TeamProjectResponse:
        project = TeamProject(
            creator_id=creator_id,
            title=data.title.strip(),
            description=(data.description.strip() or None) if data.description else None,
            tech_stack=self._normalize_tech_stack(data.tech_stack),
            poster_url=(data.poster_url.strip() or None) if data.poster_url else None,
            max_members=data.max_members,
            college=self._normalize_college(data.college),
            require_same_college=data.require_same_college,
        )
        project = self.team_repo.create(project)
        self.team_repo.add_member(project.id, creator_id, role="creator")

        for skill_data in data.required_skills:
            skill = self.skill_repo.get_or_create_by_name(
                skill_data.name.strip().lower(), skill_data.category
            )
            self.team_repo.add_required_skill(project.id, skill.id)

        self._refresh_embedding(project.id)
        return self.to_response(self.team_repo.get_by_id(project.id))

    def list_projects(
        self, skip: int = 0, limit: int = 20, college: str | None = None, q: str | None = None
    ) -> list[TeamProjectResponse]:
        projects = self.team_repo.list_projects(skip=skip, limit=limit, college=college, q=q)
        return [self.to_response(p) for p in projects]

    def get_detail(self, project_id: int, viewer_id: int | None) -> TeamProjectDetailResponse:
        project = self.team_repo.get_by_id(project_id)
        if project is None:
            raise NotFoundException("Team project not found")
        return self.to_detail(project, viewer_id)

    def update_project(
        self, requester_id: int, project_id: int, data: TeamProjectUpdate
    ) -> TeamProjectResponse:
        project = self._get_owned_project(requester_id, project_id)
        update_data = data.model_dump(exclude_unset=True)

        if "title" in update_data and update_data["title"] is not None:
            update_data["title"] = update_data["title"].strip()
        if "description" in update_data:
            update_data["description"] = (
                update_data["description"].strip() or None
            ) if update_data["description"] else None
        if "tech_stack" in update_data and update_data["tech_stack"] is not None:
            update_data["tech_stack"] = self._normalize_tech_stack(update_data["tech_stack"])
        if "poster_url" in update_data:
            update_data["poster_url"] = (
                update_data["poster_url"].strip() or None
            ) if update_data["poster_url"] else None
        if "college" in update_data:
            update_data["college"] = self._normalize_college(update_data["college"])

        new_max = update_data.get("max_members")
        if new_max is not None:
            member_count = self.team_repo.count_members(project_id)
            if new_max < member_count:
                raise ValidationException(
                    f"max_members cannot be less than current member count ({member_count})"
                )

        new_flag = update_data.get("require_same_college")
        if new_flag is True:
            college = update_data.get("college", project.college)
            if not (college or "").strip():
                raise ValidationException(
                    "college is required when require_same_college is true"
                )

        if update_data:
            self.team_repo.update(project, update_data)
        self._refresh_embedding(project_id)
        return self.to_response(self.team_repo.get_by_id(project_id))

    def delete_project(self, requester_id: int, project_id: int) -> None:
        project = self._get_owned_project(requester_id, project_id)
        self.team_repo.delete(project)

    def add_required_skill(
        self, requester_id: int, project_id: int, name: str, category
    ) -> TeamProjectResponse:
        project = self._get_owned_project(requester_id, project_id)
        skill = self.skill_repo.get_or_create_by_name(name.strip().lower(), category)
        existing = self.team_repo.get_required_skills(project_id)
        if any(link.skill_id == skill.id for link in existing):
            raise ConflictException(f"Skill '{skill.name}' is already required")
        self.team_repo.add_required_skill(project_id, skill.id)
        self._refresh_embedding(project_id)
        return self.to_response(self.team_repo.get_by_id(project.id))

    def remove_required_skill(
        self, requester_id: int, project_id: int, skill_id: int
    ) -> TeamProjectResponse:
        project = self._get_owned_project(requester_id, project_id)
        self.team_repo.remove_required_skill(project_id, skill_id)
        self._refresh_embedding(project_id)
        return self.to_response(self.team_repo.get_by_id(project.id))

    def apply(
        self, user_id: int, project_id: int, message: str | None
    ) -> TeamApplicationResponse:
        project = self._get_project_or_404(project_id)
        if project.creator_id == user_id:
            raise ValidationException("Project creator cannot apply to their own project")
        if self.team_repo.get_membership(project_id, user_id) is not None:
            raise ConflictException("You are already a member of this team")

        existing = self.team_repo.get_application(project_id, user_id)
        if existing is not None and existing.status == TeamRequestStatus.PENDING:
            raise ConflictException("You already have a pending application")

        self._check_capacity(project)
        self._check_college(project, user_id)

        if existing is not None:
            application = self.team_repo.reset_application(existing, message)
        else:
            application = self.team_repo.create_application(project_id, user_id, message)
        return self._to_application_response(application)

    def list_applications(
        self, requester_id: int, project_id: int, status: TeamRequestStatus | None = None
    ) -> list[TeamApplicationResponse]:
        self._get_owned_project(requester_id, project_id)
        applications = self.team_repo.list_applications(project_id, status=status)
        return [self._to_application_response(a) for a in applications]

    def accept_application(
        self, requester_id: int, project_id: int, application_id: int
    ) -> TeamApplicationResponse:
        project = self._get_owned_project(requester_id, project_id)
        application = self.team_repo.get_application_by_id(application_id)
        if application is None or application.team_project_id != project_id:
            raise NotFoundException("Application not found")
        if application.status != TeamRequestStatus.PENDING:
            raise ValidationException("Application is not pending")
        if self.team_repo.get_membership(project_id, application.user_id) is not None:
            raise ConflictException("Applicant is already a member")

        self._check_capacity(project)
        self._check_college(project, application.user_id)

        self.team_repo.add_member(project_id, application.user_id, role="member")
        application = self.team_repo.set_application_status(
            application, TeamRequestStatus.ACCEPTED
        )
        pending_invite = self.team_repo.get_invitation(project_id, application.user_id)
        if pending_invite is not None and pending_invite.status == TeamRequestStatus.PENDING:
            self.team_repo.set_invitation_status(
                pending_invite, TeamRequestStatus.ACCEPTED
            )
        return self._to_application_response(application)

    def reject_application(
        self, requester_id: int, project_id: int, application_id: int
    ) -> TeamApplicationResponse:
        self._get_owned_project(requester_id, project_id)
        application = self.team_repo.get_application_by_id(application_id)
        if application is None or application.team_project_id != project_id:
            raise NotFoundException("Application not found")
        if application.status != TeamRequestStatus.PENDING:
            raise ValidationException("Application is not pending")
        application = self.team_repo.set_application_status(
            application, TeamRequestStatus.REJECTED
        )
        return self._to_application_response(application)

    def invite(
        self, requester_id: int, project_id: int, invitee_id: int, message: str | None
    ) -> TeamInvitationResponse:
        project = self._get_owned_project(requester_id, project_id)
        invitee = self.user_repo.get_by_id(invitee_id)
        if invitee is None:
            raise NotFoundException("User not found")
        if invitee_id == project.creator_id:
            raise ValidationException("Cannot invite the project creator")
        if self.team_repo.get_membership(project_id, invitee_id) is not None:
            raise ConflictException("User is already a member of this team")

        existing = self.team_repo.get_invitation(project_id, invitee_id)
        if existing is not None and existing.status == TeamRequestStatus.PENDING:
            raise ConflictException("User already has a pending invitation")

        self._check_capacity(project)
        self._check_college(project, invitee_id)

        if existing is not None:
            invitation = self.team_repo.reset_invitation(existing, message)
        else:
            invitation = self.team_repo.create_invitation(
                project_id, requester_id, invitee_id, message
            )
        return self._to_invitation_response(invitation, invitee.username)

    def list_my_applications(self, user_id: int) -> list[TeamApplicationResponse]:
        applications = self.team_repo.list_user_applications(user_id)
        return [self._to_application_response(a) for a in applications]

    def list_my_invitations(
        self, user_id: int, username: str
    ) -> list[TeamInvitationResponse]:
        invitations = self.team_repo.list_user_invitations(user_id)
        return [self._to_invitation_response(i, username) for i in invitations]

    def accept_invitation(
        self, requester_id: int, invitation_id: int
    ) -> TeamInvitationResponse:
        invitation = self.team_repo.get_invitation_by_id(invitation_id)
        if invitation is None:
            raise NotFoundException("Invitation not found")
        if invitation.invitee_id != requester_id:
            raise ForbiddenException("You cannot accept someone else's invitation")
        if invitation.status != TeamRequestStatus.PENDING:
            raise ValidationException("Invitation is not pending")

        project = self._get_project_or_404(invitation.team_project_id)
        if self.team_repo.get_membership(project.id, requester_id) is not None:
            raise ConflictException("You are already a member of this team")

        self._check_capacity(project)
        self._check_college(project, requester_id)

        self.team_repo.add_member(project.id, requester_id, role="member")
        invitation = self.team_repo.set_invitation_status(
            invitation, TeamRequestStatus.ACCEPTED
        )
        pending_app = self.team_repo.get_application(project.id, requester_id)
        if pending_app is not None and pending_app.status == TeamRequestStatus.PENDING:
            self.team_repo.set_application_status(
                pending_app, TeamRequestStatus.ACCEPTED
            )

        invitee = self.user_repo.get_by_id(requester_id)
        return self._to_invitation_response(
            invitation, invitee.username if invitee else None
        )

    def reject_invitation(
        self, requester_id: int, invitation_id: int
    ) -> TeamInvitationResponse:
        invitation = self.team_repo.get_invitation_by_id(invitation_id)
        if invitation is None:
            raise NotFoundException("Invitation not found")
        if invitation.invitee_id != requester_id:
            raise ForbiddenException("You cannot reject someone else's invitation")
        if invitation.status != TeamRequestStatus.PENDING:
            raise ValidationException("Invitation is not pending")
        invitation = self.team_repo.set_invitation_status(
            invitation, TeamRequestStatus.REJECTED
        )
        invitee = self.user_repo.get_by_id(requester_id)
        return self._to_invitation_response(
            invitation, invitee.username if invitee else None
        )

    def remove_member(
        self, requester_id: int, project_id: int, target_user_id: int
    ) -> None:
        project = self._get_project_or_404(project_id)
        membership = self.team_repo.get_membership(project_id, target_user_id)
        if membership is None:
            raise NotFoundException("User is not a member of this team")

        if target_user_id == requester_id:
            if project.creator_id == requester_id:
                raise ValidationException(
                    "Creator cannot leave the team; delete the project instead"
                )
        else:
            if project.creator_id != requester_id:
                raise ForbiddenException("Only the project creator can remove members")
            if target_user_id == project.creator_id:
                raise ValidationException("Creator cannot be removed from the team")

        self.team_repo.remove_member(membership)

    def to_response(self, project) -> TeamProjectResponse:
        required = self.team_repo.get_required_skills(project.id)
        member_count = self.team_repo.count_members(project.id)
        return TeamProjectResponse(
            id=project.id,
            creator_id=project.creator_id,
            title=project.title,
            description=project.description,
            tech_stack=project.tech_stack or [],
            poster_url=project.poster_url,
            max_members=project.max_members,
            member_count=member_count,
            college=project.college,
            require_same_college=project.require_same_college,
            required_skills=[
                SkillBrief(id=link.skill.id, name=link.skill.name, category=link.skill.category)
                for link in required
            ],
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    def to_detail(self, project, viewer_id: int | None) -> TeamProjectDetailResponse:
        base = self.to_response(project)
        memberships = self.team_repo.list_members(project.id)
        members = [
            TeamMemberResponse(
                user_id=m.user_id,
                username=m.user.username,
                full_name=m.user.profile.full_name if m.user.profile else None,
                role=m.role,
                joined_at=m.joined_at,
            )
            for m in memberships
        ]

        is_creator = viewer_id is not None and project.creator_id == viewer_id
        is_member = False
        application_status = None
        invitation_status = None
        if viewer_id is not None:
            is_member = (
                self.team_repo.get_membership(project.id, viewer_id) is not None
            )
            application = self.team_repo.get_application(project.id, viewer_id)
            application_status = application.status if application else None
            invitation = self.team_repo.get_invitation(project.id, viewer_id)
            invitation_status = invitation.status if invitation else None

        return TeamProjectDetailResponse(
            **base.model_dump(),
            members=members,
            is_creator=is_creator,
            is_member=is_member,
            application_status=application_status,
            invitation_status=invitation_status,
        )

    def _get_project_or_404(self, project_id: int):
        project = self.team_repo.get_by_id(project_id)
        if project is None:
            raise NotFoundException("Team project not found")
        return project

    def _get_owned_project(self, requester_id: int, project_id: int):
        project = self._get_project_or_404(project_id)
        if project.creator_id != requester_id:
            raise ForbiddenException("Only the project creator can do this")
        return project

    def _check_capacity(self, project) -> None:
        member_count = self.team_repo.count_members(project.id)
        if member_count >= project.max_members:
            raise ValidationException("Team is full")

    def _check_college(self, project, user_id: int) -> None:
        if not project.require_same_college:
            return
        profile = self.profile_repo.get_by_user_id(user_id)
        user_college = (
            profile.college.strip().lower()
            if profile and profile.college
            else ""
        )
        wanted = (project.college or "").strip().lower()
        if not user_college or user_college != wanted:
            raise ValidationException(
                f"This project requires teammates from {project.college}"
            )

    def _refresh_embedding(self, project_id: int) -> None:
        project = self.team_repo.get_by_id(project_id)
        if project is None:
            return
        required = self.team_repo.get_required_skills(project_id)
        project.embedding = self.embedding_service.embed_team_project(
            project, required
        )
        project.embedding_updated_at = datetime.now(timezone.utc)
        self.db.commit()

    def _normalize_tech_stack(self, tech_stack: list[str] | None) -> list[str]:
        if not tech_stack:
            return []
        seen: set[str] = set()
        result: list[str] = []
        for item in tech_stack:
            cleaned = (item or "").strip()
            if not cleaned or len(cleaned) > 50:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(cleaned)
        return result[:30]

    def _normalize_college(self, college: str | None) -> str | None:
        if college is None:
            return None
        cleaned = college.strip()
        return cleaned or None

    def _to_application_response(self, application) -> TeamApplicationResponse:
        profile = self.profile_repo.get_by_user_id(application.user_id)
        username = None
        if application.user is not None:
            username = application.user.username
        else:
            user = self.user_repo.get_by_id(application.user_id)
            username = user.username if user else None
        return TeamApplicationResponse(
            id=application.id,
            team_project_id=application.team_project_id,
            user_id=application.user_id,
            username=username or "",
            full_name=profile.full_name if profile else None,
            message=application.message,
            status=application.status,
            created_at=application.created_at,
        )

    def _to_invitation_response(
        self, invitation, username: str | None
    ) -> TeamInvitationResponse:
        project_title = ""
        if invitation.team_project is not None:
            project_title = invitation.team_project.title
        else:
            project = self.team_repo.get_by_id(invitation.team_project_id)
            project_title = project.title if project else ""
        return TeamInvitationResponse(
            id=invitation.id,
            team_project_id=invitation.team_project_id,
            project_title=project_title,
            inviter_id=invitation.inviter_id,
            invitee_id=invitation.invitee_id,
            username=username,
            message=invitation.message,
            status=invitation.status,
            created_at=invitation.created_at,
        )
