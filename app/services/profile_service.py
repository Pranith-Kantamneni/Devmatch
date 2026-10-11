from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core import cache as result_cache
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
        if "college_id" in update_data or "college" in update_data:
            from app.core.exceptions import ValidationException
            from app.data.colleges import resolve_input

            try:
                cid, display = resolve_input(
                    update_data.pop("college_id", None),
                    update_data.pop("college", None),
                )
            except ValueError as exc:
                raise ValidationException(str(exc))
            # Only overwrite when the caller actually sent college fields;
            # clearing is done by sending college_id=null + college=null.
            if "college_id" in data.model_fields_set or "college" in data.model_fields_set:
                update_data["college_id"] = cid
                update_data["college"] = display
        if update_data:
            self.profile_repo.update(profile, update_data)

        self._refresh_embedding(user_id)
        return self.get_own_profile(user_id)

    def add_skill(self, user_id: int, data: SkillAdd) -> ProfileResponse:
        self._ensure_profile(user_id)

        normalized_name = data.name.strip().lower()
        if not normalized_name:
            from app.core.exceptions import ValidationException

            raise ValidationException("Skill name must not be blank")

        try:
            skill = self.skill_repo.get_or_create_by_name(normalized_name, data.category)
        except Exception:
            raise

        existing = self.profile_repo.get_user_skills(user_id)
        if any(us.skill_id == skill.id for us in existing):
            raise ConflictException(f"Skill '{skill.name}' already added")

        try:
            self.skill_repo.add_user_skill(
                user_id, skill.id, data.proficiency, data.years_experience
            )
        except Exception:
            # Concurrent duplicate add violates the unique constraint.
            from sqlalchemy.exc import IntegrityError

            from app.core.exceptions import ValidationException as VE

            self.db.rollback()
            raise ConflictException(f"Skill '{skill.name}' already added")
        self._refresh_embedding(user_id)
        return self.get_own_profile(user_id)

    def remove_skill(self, user_id: int, skill_id: int) -> ProfileResponse:
        removed = self.skill_repo.remove_user_skill(user_id, skill_id)
        if not removed:
            raise NotFoundException("Skill not found on your profile")
        self._refresh_embedding(user_id)
        return self.get_own_profile(user_id)

    def add_project(self, user_id: int, data: ProjectAdd) -> ProfileResponse:
        self._ensure_profile(user_id)

        title = (data.title or "").strip()
        if not title:
            from app.core.exceptions import ValidationException

            raise ValidationException("Project title must not be blank")

        project = self.skill_repo.create_project(
            user_id, title, data.description, data.url
        )

        seen: set[str] = set()
        for raw_name in data.skill_names:
            cleaned = (raw_name or "").strip().lower()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            skill = self.skill_repo.get_or_create_by_name(
                cleaned, SkillCategory.OTHER
            )
            self.skill_repo.add_project_skill(project.id, skill.id)

        self._refresh_embedding(user_id)
        return self.get_own_profile(user_id)

    def remove_project(self, user_id: int, project_id: int) -> ProfileResponse:
        removed = self.skill_repo.remove_project(project_id, user_id)
        if not removed:
            raise NotFoundException("Project not found")
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
        # Profile content changed → drop cached recommendations for this user.
        result_cache.bump_version(result_cache.user_scope(user_id))
