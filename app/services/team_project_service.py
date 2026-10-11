from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core import cache as result_cache
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
from app.schemas.chat import (
    ApplicationMessageResponse,
    PollCreate,
    PollOptionResponse,
    PollResponse,
    PollVote,
    TeamMessageResponse,
)
from app.schemas.skill import SkillBrief
from app.schemas.team_project import (
    TeamApplicationResponse,
    TeamInvitationResponse,
    TeamMemberResponse,
    TeamProjectCreate,
    TeamProjectDetailResponse,
    TeamProjectResponse,
    TeamProjectUpdate,
    TeamSkillGaps,
    SkillGapEntry,
)
from app.services.embedding_service import EmbeddingService
from app.services.matching_service import normalize_skill_name


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
        title = (data.title or "").strip()
        if not title:
            raise ValidationException("Project title must not be blank")
        college_id, college = self._resolve_college(data.college_id, data.college)
        project = TeamProject(
            creator_id=creator_id,
            title=title,
            description=(data.description.strip() or None) if data.description else None,
            tech_stack=self._normalize_tech_stack(data.tech_stack),
            poster_url=(data.poster_url.strip() or None) if data.poster_url else None,
            max_members=data.max_members,
            college=college,
            college_id=college_id,
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
            update_data["title"] = (update_data["title"] or "").strip()
            if not update_data["title"]:
                raise ValidationException("Project title must not be blank")
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
        if "college" in update_data or "college_id" in update_data:
            cid, display = self._resolve_college(
                update_data.pop("college_id", None),
                update_data.pop("college", None),
            )
            update_data["college_id"] = cid
            update_data["college"] = display

        new_max = update_data.get("max_members")
        if new_max is not None:
            member_count = self.team_repo.count_members(project_id)
            if new_max < member_count:
                raise ValidationException(
                    f"max_members cannot be less than current member count ({member_count})"
                )

        new_flag = update_data.get("require_same_college")
        effective_flag = new_flag if new_flag is not None else project.require_same_college
        if effective_flag is True:
            college = update_data.get("college", project.college)
            college_id = update_data.get("college_id", project.college_id)
            if not (college or "").strip() and not (college_id or "").strip():
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
        cleaned = (name or "").strip().lower()
        if not cleaned:
            raise ValidationException("Skill name must not be blank")
        skill = self.skill_repo.get_or_create_by_name(cleaned, category)
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
        removed = self.team_repo.remove_required_skill(project_id, skill_id)
        if not removed:
            raise NotFoundException("Required skill not found on this project")
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
        norms, display = self._required_norms(project_id)
        return self._to_application_response(
            application, fit=self._fit_for_user(user_id, norms, display)
        )

    def list_applications(
        self, requester_id: int, project_id: int, status: TeamRequestStatus | None = None
    ) -> list[TeamApplicationResponse]:
        self._get_owned_project(requester_id, project_id)
        applications = self.team_repo.list_applications(project_id, status=status)
        norms, display = self._required_norms(project_id)
        return [
            self._to_application_response(
                a, fit=self._fit_for_user(a.user_id, norms, display)
            )
            for a in applications
        ]

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
        norms, display = self._required_norms(project_id)
        return self._to_application_response(
            application,
            fit=self._fit_for_user(application.user_id, norms, display),
        )

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
        norms, display = self._required_norms(project_id)
        return self._to_application_response(
            application,
            fit=self._fit_for_user(application.user_id, norms, display),
        )

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

    # -- chat ------------------------------------------------------

    def _require_membership(self, project_id: int, user_id: int):
        project = self._get_project_or_404(project_id)
        is_member = self.team_repo.get_membership(project_id, user_id) is not None
        if not is_member and project.creator_id != user_id:
            raise ForbiddenException("Only team members can access the team chat")
        return project

    def _require_chat_unlocked(self, project_id: int, user_id: int):
        """Team chat (messages + polls) opens once a second member joins."""
        project = self._require_membership(project_id, user_id)
        if self.team_repo.count_members(project_id) < 2:
            raise ForbiddenException(
                "Team chat unlocks once a second member joins the team"
            )
        return project

    def list_team_messages(
        self, requester_id: int, project_id: int, limit: int, before_id: int | None
    ) -> list[TeamMessageResponse]:
        self._require_chat_unlocked(project_id, requester_id)
        return [
            self._to_team_message_response(m)
            for m in self.team_repo.list_team_messages(project_id, limit, before_id)
        ]

    def post_team_message(
        self, requester_id: int, project_id: int, body: str
    ) -> TeamMessageResponse:
        self._require_chat_unlocked(project_id, requester_id)
        sender = self.user_repo.get_by_id(requester_id)
        message = self.team_repo.create_team_message(
            project_id,
            requester_id,
            sender.username if sender else "Someone",
            self._clean_message_body(body),
        )
        return self._to_team_message_response(message)

    def _require_application_thread(
        self, requester_id: int, project_id: int, application_id: int
    ):
        project = self._get_project_or_404(project_id)
        application = self.team_repo.get_application_by_id(application_id)
        if application is None or application.team_project_id != project_id:
            raise NotFoundException("Application not found")
        if requester_id != project.creator_id and requester_id != application.user_id:
            raise ForbiddenException("Only the applicant and creator can view this chat")
        return application

    def list_application_messages(
        self,
        requester_id: int,
        project_id: int,
        application_id: int,
        limit: int,
        before_id: int | None,
    ) -> list[ApplicationMessageResponse]:
        self._require_application_thread(requester_id, project_id, application_id)
        return [
            self._to_application_message_response(m)
            for m in self.team_repo.list_application_messages(
                application_id, limit, before_id
            )
        ]

    def post_application_message(
        self, requester_id: int, project_id: int, application_id: int, body: str
    ) -> ApplicationMessageResponse:
        application = self._require_application_thread(
            requester_id, project_id, application_id
        )
        sender = self.user_repo.get_by_id(requester_id)
        message = self.team_repo.create_application_message(
            project_id,
            application.id,
            requester_id,
            sender.username if sender else "Someone",
            self._clean_message_body(body),
        )
        return self._to_application_message_response(message)

    @staticmethod
    def _clean_message_body(body: str | None) -> str:
        cleaned = (body or "").strip()
        if not cleaned:
            raise ValidationException("Message must not be empty")
        if len(cleaned) > 2000:
            raise ValidationException("Message is too long (max 2000 characters)")
        return cleaned

    @staticmethod
    def _to_team_message_response(message) -> TeamMessageResponse:
        return TeamMessageResponse(
            id=message.id,
            team_project_id=message.team_project_id,
            sender_id=message.sender_id,
            sender_username=message.sender_username or "Someone",
            body=message.body,
            created_at=message.created_at,
        )

    @staticmethod
    def _to_application_message_response(message) -> ApplicationMessageResponse:
        return ApplicationMessageResponse(
            id=message.id,
            team_project_id=message.team_project_id,
            application_id=message.application_id,
            sender_id=message.sender_id,
            sender_username=message.sender_username or "Someone",
            body=message.body,
            created_at=message.created_at,
        )

    # -- polls -------------------------------------------------------

    def list_polls(self, requester_id: int, project_id: int) -> list[PollResponse]:
        self._require_chat_unlocked(project_id, requester_id)
        polls = self.team_repo.list_polls(project_id)
        return [self._to_poll_response(p, requester_id) for p in polls]

    def create_poll(
        self, requester_id: int, project_id: int, data: PollCreate
    ) -> PollResponse:
        self._require_chat_unlocked(project_id, requester_id)
        question = (data.question or "").strip()
        if not question:
            raise ValidationException("Poll question must not be empty")
        seen: set[str] = set()
        options: list[str] = []
        for raw in data.options or []:
            text = (raw or "").strip()
            if not text or len(text) > 120:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            options.append(text)
        if len(options) < 2:
            raise ValidationException("A poll needs at least 2 different options")
        sender = self.user_repo.get_by_id(requester_id)
        poll = self.team_repo.create_poll(
            project_id,
            requester_id,
            sender.username if sender else "Someone",
            question,
            options[:6],
        )
        return self._to_poll_response(poll, requester_id)

    def vote_poll(
        self, requester_id: int, project_id: int, poll_id: int, data: PollVote
    ) -> PollResponse:
        self._require_chat_unlocked(project_id, requester_id)
        poll = self._get_poll_or_404(project_id, poll_id)
        if poll.is_closed:
            raise ValidationException("This poll is closed")
        if not any(o.id == data.option_id for o in poll.options):
            raise ValidationException("Unknown poll option")
        self.team_repo.cast_vote(poll_id, data.option_id, requester_id)
        return self._to_poll_response(
            self.team_repo.get_poll(poll_id), requester_id
        )

    def close_poll(
        self, requester_id: int, project_id: int, poll_id: int
    ) -> PollResponse:
        project = self._require_chat_unlocked(project_id, requester_id)
        poll = self._get_poll_or_404(project_id, poll_id)
        if requester_id != project.creator_id and requester_id != poll.creator_id:
            raise ForbiddenException("Only the team creator or poll creator can close it")
        return self._to_poll_response(
            self.team_repo.close_poll(poll), requester_id
        )

    def _get_poll_or_404(self, project_id: int, poll_id: int):
        poll = self.team_repo.get_poll(poll_id)
        if poll is None or poll.team_project_id != project_id:
            raise NotFoundException("Poll not found")
        return poll

    def _to_poll_response(self, poll, voter_id: int) -> PollResponse:
        counts = self.team_repo.vote_counts(poll.id)
        options = sorted(poll.options, key=lambda o: o.position)
        return PollResponse(
            id=poll.id,
            team_project_id=poll.team_project_id,
            creator_id=poll.creator_id,
            creator_username=poll.creator_username or "Someone",
            question=poll.question,
            is_closed=poll.is_closed,
            created_at=poll.created_at,
            total_votes=sum(counts.values()),
            options=[
                PollOptionResponse(id=o.id, text=o.text, votes=counts.get(o.id, 0))
                for o in options
            ],
            my_option_id=self.team_repo.voter_option(poll.id, voter_id),
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
        if project is None:
            raise NotFoundException("Team project not found")
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
            college_id=project.college_id,
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
        application_id = None
        invitation_status = None
        if viewer_id is not None:
            is_member = (
                self.team_repo.get_membership(project.id, viewer_id) is not None
            )
            application = self.team_repo.get_application(project.id, viewer_id)
            application_status = application.status if application else None
            application_id = application.id if application else None
            invitation = self.team_repo.get_invitation(project.id, viewer_id)
            invitation_status = invitation.status if invitation else None

        return TeamProjectDetailResponse(
            **base.model_dump(),
            members=members,
            is_creator=is_creator,
            is_member=is_member,
            application_status=application_status,
            application_id=application_id,
            invitation_status=invitation_status,
        )

    def get_skill_gaps(
        self, requester_id: int, project_id: int
    ) -> TeamSkillGaps:
        """Which required skills the current roster covers — the hiring checklist."""
        project = self._get_owned_project(requester_id, project_id)
        norms, display = self._required_norms(project_id)
        memberships = self.team_repo.list_members(project_id)
        member_ids = [m.user_id for m in memberships] + [project.creator_id]

        covered_count: dict[str, int] = {norm: 0 for norm in norms}
        for user_id in member_ids:
            for norm in self._user_skill_norms(user_id):
                if norm in covered_count:
                    covered_count[norm] += 1

        covered = sorted(display[n] for n, c in covered_count.items() if c > 0)
        uncovered = sorted(display[n] for n, c in covered_count.items() if c == 0)
        return TeamSkillGaps(
            total_required=len(norms),
            covered_skills=covered,
            uncovered_skills=uncovered,
            coverage=round(len(covered) / len(norms), 4) if norms else 0.0,
            by_skill=[
                SkillGapEntry(skill=display[n], covered_by_members=covered_count[n])
                for n in sorted(norms, key=lambda n: (covered_count[n], display[n].lower()))
            ],
        )

    def _required_norms(self, project_id: int) -> tuple[set[str], dict[str, str]]:
        """Required skills + tech stack as (normalized set, norm → display name)."""
        project = self.team_repo.get_by_id(project_id)
        names = [link.skill.name for link in self.team_repo.get_required_skills(project_id)]
        if project and project.tech_stack:
            names.extend(project.tech_stack)
        display: dict[str, str] = {}
        for name in names:
            if not (name or "").strip():
                continue
            display.setdefault(normalize_skill_name(name), name.strip())
        return set(display.keys()), display

    def _user_skill_norms(self, user_id: int) -> set[str]:
        norms = {
            normalize_skill_name(us.skill.name)
            for us in self.profile_repo.get_user_skills(user_id)
            if us.skill and us.skill.name
        }
        for portfolio_project in self.profile_repo.get_user_projects(user_id):
            for link in portfolio_project.skills or []:
                skill = getattr(link, "skill", None)
                if skill is not None and skill.name:
                    norms.add(normalize_skill_name(skill.name))
        return norms

    def _fit_for_user(
        self, user_id: int, norms: set[str], display: dict[str, str]
    ) -> tuple[float, list[str]]:
        if not norms:
            return 0.0, []
        matched = norms & self._user_skill_norms(user_id)
        return (
            round(len(matched) / len(norms), 4),
            sorted(display[n] for n in matched),
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
        from app.data.colleges import same_college

        profile = self.profile_repo.get_by_user_id(user_id)
        user_college = profile.college if profile else None
        user_college_id = profile.college_id if profile else None
        if not same_college(
            user_college,
            user_college_id,
            project.college,
            project.college_id,
        ):
            raise ValidationException(
                f"This project requires teammates from {project.college}"
            )

    @staticmethod
    def _resolve_college(
        college_id: str | None, college_text: str | None
    ) -> tuple[str | None, str | None]:
        from app.data.colleges import resolve_input

        try:
            return resolve_input(college_id, college_text)
        except ValueError as exc:
            raise ValidationException(str(exc))

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
        result_cache.bump_version(result_cache.project_scope(project_id))

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

    def _to_application_response(
        self, application, fit: tuple[float, list[str]] | None = None
    ) -> TeamApplicationResponse:
        profile = self.profile_repo.get_by_user_id(application.user_id)
        username = None
        if application.user is not None:
            username = application.user.username
        else:
            user = self.user_repo.get_by_id(application.user_id)
            username = user.username if user else None
        project_title = None
        if getattr(application, "team_project", None) is not None:
            project_title = application.team_project.title
        else:
            project = self.team_repo.get_by_id(application.team_project_id)
            project_title = project.title if project else None
        coverage, matched = fit if fit is not None else (0.0, [])
        return TeamApplicationResponse(
            id=application.id,
            team_project_id=application.team_project_id,
            project_title=project_title,
            user_id=application.user_id,
            username=username or "",
            full_name=profile.full_name if profile else None,
            message=application.message,
            status=application.status,
            created_at=application.created_at,
            coverage=coverage,
            matched_skills=matched,
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
