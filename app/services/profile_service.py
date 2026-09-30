from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import ConflictException, NotFoundException
from app.db.models.profile import DeveloperProfile
from app.db.models.skill import SkillCategory
from app.repositories.profile_repository import ProfileRepository
from app.repositories.skill_repository import SkillRepository
from app.schemas.profile import (
    ProfileResponse,
    ProfileUpdate,
    ProjectAdd,
    PublicProfileResponse,
)
from app.schemas.skill import SkillAdd
from app.services.embedding_service import EmbeddingService
from app.utils.mappers import to_profile_response, to_public_profile_response


class ProfileService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        embedding_service: EmbeddingService,
    ):
        self.db = db
        self.settings = settings
        self.embedding_service = embedding_service
        self.profile_repo = ProfileRepository(db)
        self.skill_repo = SkillRepository(db)

    def get_own_profile(self, user_id: int) -> ProfileResponse:
        profile = self.profile_repo.get_by_user_id_with_relations(user_id)
        if profile is None:
            raise NotFoundException("Profile not found")
        return to_profile_response(profile)

    def get_public_profile(self, user_id: int) -> PublicProfileResponse:
        profile = self.profile_repo.get_by_user_id_with_relations(user_id)
        if profile is None:
            raise NotFoundException("Profile not found")
        return to_public_profile_response(profile)

    def update_profile(self, user_id: int, data: ProfileUpdate) -> ProfileResponse:
        profile = self.profile_repo.get_by_user_id(user_id)
        if profile is None:
            profile = self.profile_repo.create(DeveloperProfile(user_id=user_id))

        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            self.profile_repo.update(profile, update_data)

        self._refresh_embedding(user_id)
        return self.get_own_profile(user_id)

    def add_skill(self, user_id: int, data: SkillAdd) -> ProfileResponse:
        self._ensure_profile(user_id)

        normalized_name = data.name.strip().lower()
        skill = self.skill_repo.get_or_create_by_name(normalized_name, data.category)

        existing = self.profile_repo.get_user_skills(user_id)
        if any(us.skill_id == skill.id for us in existing):
            raise ConflictException(f"Skill '{skill.name}' already added")

        self.skill_repo.add_user_skill(
            user_id, skill.id, data.proficiency, data.years_experience
        )
        self._refresh_embedding(user_id)
        return self.get_own_profile(user_id)

    def remove_skill(self, user_id: int, skill_id: int) -> ProfileResponse:
        self.skill_repo.remove_user_skill(user_id, skill_id)
        self._refresh_embedding(user_id)
        return self.get_own_profile(user_id)

    def add_project(self, user_id: int, data: ProjectAdd) -> ProfileResponse:
        self._ensure_profile(user_id)

        project = self.skill_repo.create_project(
            user_id, data.title, data.description, data.url
        )

        for name in data.skill_names:
            skill = self.skill_repo.get_or_create_by_name(
                name.strip().lower(), SkillCategory.OTHER
            )
            self.skill_repo.add_project_skill(project.id, skill.id)

        self._refresh_embedding(user_id)
        return self.get_own_profile(user_id)

    def remove_project(self, user_id: int, project_id: int) -> ProfileResponse:
        self.skill_repo.remove_project(project_id, user_id)
        self._refresh_embedding(user_id)
        return self.get_own_profile(user_id)

    def _ensure_profile(self, user_id: int) -> None:
        profile = self.profile_repo.get_by_user_id(user_id)
        if profile is None:
            self.profile_repo.create(DeveloperProfile(user_id=user_id))

    def _refresh_embedding(self, user_id: int) -> None:
        profile = self.profile_repo.get_by_user_id(user_id)
        if profile is None:
            return

        user_skills = self.profile_repo.get_user_skills(user_id)
        projects = self.profile_repo.get_user_projects(user_id)

        profile.embedding = self.embedding_service.embed_profile(
            profile, user_skills, projects
        )
        profile.embedding_updated_at = datetime.now(timezone.utc)
        self.db.commit()
