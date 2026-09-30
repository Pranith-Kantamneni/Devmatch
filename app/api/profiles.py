from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user, get_db
from app.core.exceptions import ValidationException
from app.db.models.user import User
from app.schemas.profile import (
    ProfileResponse,
    ProfileUpdate,
    ProjectAdd,
    PublicProfileResponse,
)
from app.schemas.resume import ParsedResume
from app.schemas.skill import SkillAdd
from app.services.embedding_service import EmbeddingService
from app.services.profile_service import ProfileService
from app.services.resume_parser import ResumeParserService

router = APIRouter(prefix="/profiles", tags=["Profiles"])

MAX_RESUME_SIZE = 10 * 1024 * 1024


def get_profile_service(db: Session = Depends(get_db)) -> ProfileService:
    settings = get_settings()
    return ProfileService(db, settings, EmbeddingService(settings))


@router.get(
    "/me",
    response_model=ProfileResponse,
    summary="Get the current user's full profile",
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    return service.get_own_profile(current_user.id)


@router.put(
    "/me",
    response_model=ProfileResponse,
    summary="Update the current user's profile",
)
def update_my_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    return service.update_profile(current_user.id, data)


@router.get(
    "/{user_id}",
    response_model=PublicProfileResponse,
    summary="Get a user's public profile",
)
def get_public_profile(
    user_id: int,
    service: ProfileService = Depends(get_profile_service),
):
    return service.get_public_profile(user_id)


@router.post(
    "/me/parse-resume",
    response_model=ParsedResume,
    summary="Parse a resume file and extract profile details",
)
def parse_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    filename = file.filename or ""
    if not filename.lower().endswith((".pdf", ".docx", ".doc", ".txt", ".md")):
        raise ValidationException("Unsupported file type. Upload a PDF, DOCX, or TXT resume.")

    content = file.file.read()
    if len(content) > MAX_RESUME_SIZE:
        raise ValidationException("File is too large. Maximum size is 10MB.")

    return ResumeParserService().parse(content, filename)


@router.post(
    "/me/skills",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a skill to the current user's profile",
)
def add_skill(
    data: SkillAdd,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    return service.add_skill(current_user.id, data)


@router.delete(
    "/me/skills/{skill_id}",
    response_model=ProfileResponse,
    summary="Remove a skill from the current user's profile",
)
def remove_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    return service.remove_skill(current_user.id, skill_id)


@router.post(
    "/me/projects",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a project to the current user's profile",
)
def add_project(
    data: ProjectAdd,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    return service.add_project(current_user.id, data)


@router.delete(
    "/me/projects/{project_id}",
    response_model=ProfileResponse,
    summary="Remove a project from the current user's profile",
)
def remove_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    return service.remove_project(current_user.id, project_id)
