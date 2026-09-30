from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user, get_db, get_optional_current_user
from app.db.models.team_project import TeamRequestStatus
from app.db.models.user import User
from app.schemas.team_project import (
    ApplyRequest,
    InviteRequest,
    ProjectRecommendationListResponse,
    TeamApplicationResponse,
    TeamInvitationResponse,
    TeamProjectCreate,
    TeamProjectDetailResponse,
    TeamProjectResponse,
    TeamProjectSkillAdd,
    TeamProjectUpdate,
)
from app.services.embedding_service import EmbeddingService
from app.services.matching_service import MatchingService
from app.services.team_project_service import TeamProjectService

router = APIRouter(prefix="/team-projects", tags=["Team Projects"])


def get_team_service(db: Session = Depends(get_db)) -> TeamProjectService:
    settings = get_settings()
    return TeamProjectService(db, settings, EmbeddingService(settings))


@router.post(
    "",
    response_model=TeamProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a team project or hackathon",
)
def create_team_project(
    data: TeamProjectCreate,
    current_user: User = Depends(get_current_user),
    service: TeamProjectService = Depends(get_team_service),
):
    return service.create_project(current_user.id, data)


@router.get(
    "",
    response_model=list[TeamProjectResponse],
    summary="Discover team projects",
)
def list_team_projects(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    college: str | None = Query(default=None),
    q: str | None = Query(default=None),
    service: TeamProjectService = Depends(get_team_service),
):
    return service.list_projects(skip=skip, limit=limit, college=college, q=q)


@router.get(
    "/me/applications",
    response_model=list[TeamApplicationResponse],
    summary="List my outgoing team applications",
)
def list_my_applications(
    current_user: User = Depends(get_current_user),
    service: TeamProjectService = Depends(get_team_service),
):
    return service.list_my_applications(current_user.id)


@router.get(
    "/me/invitations",
    response_model=list[TeamInvitationResponse],
    summary="List my incoming team invitations",
)
def list_my_invitations(
    current_user: User = Depends(get_current_user),
    service: TeamProjectService = Depends(get_team_service),
):
    return service.list_my_invitations(current_user.id, current_user.username)


@router.post(
    "/invitations/{invitation_id}/accept",
    response_model=TeamInvitationResponse,
    summary="Accept a team invitation",
)
def accept_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    service: TeamProjectService = Depends(get_team_service),
):
    return service.accept_invitation(current_user.id, invitation_id)


@router.post(
    "/invitations/{invitation_id}/reject",
    response_model=TeamInvitationResponse,
    summary="Reject a team invitation",
)
def reject_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    service: TeamProjectService = Depends(get_team_service),
):
    return service.reject_invitation(current_user.id, invitation_id)


@router.get(
    "/{project_id}",
    response_model=TeamProjectDetailResponse,
    summary="Get a team project with viewer-specific status",
)
def get_team_project(
    project_id: int,
    viewer: User | None = Depends(get_optional_current_user),
    service: TeamProjectService = Depends(get_team_service),
):
    return service.get_detail(project_id, viewer.id if viewer else None)


@router.put(
    "/{project_id}",
    response_model=TeamProjectResponse,
    summary="Update a team project (creator only)",
)
def update_team_project(
    project_id: int,
    data: TeamProjectUpdate,
    current_user: User = Depends(get_current_user),
    service: TeamProjectService = Depends(get_team_service),
):
    return service.update_project(current_user.id, project_id, data)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a team project (creator only)",
)
def delete_team_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: TeamProjectService = Depends(get_team_service),
):
    service.delete_project(current_user.id, project_id)
    return None


@router.post(
    "/{project_id}/skills",
    response_model=TeamProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a required skill (creator only)",
)
def add_required_skill(
    project_id: int,
    data: TeamProjectSkillAdd,
    current_user: User = Depends(get_current_user),
    service: TeamProjectService = Depends(get_team_service),
):
    return service.add_required_skill(
        current_user.id, project_id, data.name, data.category
    )


@router.delete(
    "/{project_id}/skills/{skill_id}",
    response_model=TeamProjectResponse,
    summary="Remove a required skill (creator only)",
)
def remove_required_skill(
    project_id: int,
    skill_id: int,
    current_user: User = Depends(get_current_user),
    service: TeamProjectService = Depends(get_team_service),
):
    return service.remove_required_skill(current_user.id, project_id, skill_id)


@router.get(
    "/{project_id}/recommendations",
    response_model=ProjectRecommendationListResponse,
    summary="Get recommended developers for a project (creator only)",
)
def get_project_recommendations(
    project_id: int,
    limit: int | None = Query(default=None, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    if limit is None:
        limit = settings.MATCHING_DEFAULT_LIMIT
    limit = min(limit, settings.MATCHING_MAX_LIMIT)
    service = MatchingService(db, settings, EmbeddingService(settings))
    return service.get_project_recommendations(project_id, current_user.id, limit)


@router.post(
    "/{project_id}/apply",
    response_model=TeamApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply to join a team",
)
def apply_to_project(
    project_id: int,
    data: ApplyRequest,
    current_user: User = Depends(get_current_user),
    service: TeamProjectService = Depends(get_team_service),
):
    return service.apply(current_user.id, project_id, data.message)


@router.get(
    "/{project_id}/applications",
    response_model=list[TeamApplicationResponse],
    summary="List applications for a project (creator only)",
)
def list_applications(
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: TeamProjectService = Depends(get_team_service),
):
    return service.list_applications(current_user.id, project_id)


@router.post(
    "/{project_id}/applications/{application_id}/accept",
    response_model=TeamApplicationResponse,
    summary="Accept an application (creator only)",
)
def accept_application(
    project_id: int,
    application_id: int,
    current_user: User = Depends(get_current_user),
    service: TeamProjectService = Depends(get_team_service),
):
    return service.accept_application(current_user.id, project_id, application_id)


@router.post(
    "/{project_id}/applications/{application_id}/reject",
    response_model=TeamApplicationResponse,
    summary="Reject an application (creator only)",
)
def reject_application(
    project_id: int,
    application_id: int,
    current_user: User = Depends(get_current_user),
    service: TeamProjectService = Depends(get_team_service),
):
    return service.reject_application(current_user.id, project_id, application_id)


@router.post(
    "/{project_id}/invite",
    response_model=TeamInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a developer (creator only)",
)
def invite_developer(
    project_id: int,
    data: InviteRequest,
    current_user: User = Depends(get_current_user),
    service: TeamProjectService = Depends(get_team_service),
):
    return service.invite(current_user.id, project_id, data.user_id, data.message)


@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member (creator) or leave the team (self)",
)
def remove_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    service: TeamProjectService = Depends(get_team_service),
):
    service.remove_member(current_user.id, project_id, user_id)
    return None
