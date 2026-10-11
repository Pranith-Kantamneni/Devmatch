from sqlalchemy.orm import Session, selectinload

from app.db.models.profile import DeveloperProfile
from app.db.models.project import Project, ProjectSkill
from app.db.models.skill import UserSkill
from app.db.models.user import User


class ProfileRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> DeveloperProfile | None:
        return (
            self.db.query(DeveloperProfile)
            .filter(DeveloperProfile.user_id == user_id)
            .first()
        )

    def get_by_user_id_with_relations(self, user_id: int) -> DeveloperProfile | None:
        return (
            self.db.query(DeveloperProfile)
            .options(self._eager_load_options())
            .filter(DeveloperProfile.user_id == user_id)
            .first()
        )

    def create(self, profile: DeveloperProfile) -> DeveloperProfile:
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def update(self, profile: DeveloperProfile, data: dict) -> DeveloperProfile:
        for key, value in data.items():
            setattr(profile, key, value)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def list_with_embeddings(self, exclude_user_id: int) -> list[DeveloperProfile]:
        return self.list_with_embeddings_excluding([exclude_user_id])

    def list_with_embeddings_excluding(
        self, exclude_user_ids: list[int]
    ) -> list[DeveloperProfile]:
        query = (
            self.db.query(DeveloperProfile)
            .options(self._eager_load_options())
            .filter(DeveloperProfile.embedding.isnot(None))
        )
        if exclude_user_ids:
            query = query.filter(~DeveloperProfile.user_id.in_(exclude_user_ids))
        return query.all()

    def get_user_skills(self, user_id: int) -> list[UserSkill]:
        return (
            self.db.query(UserSkill)
            .options(selectinload(UserSkill.skill))
            .filter(UserSkill.user_id == user_id)
            .all()
        )

    def get_user_projects(self, user_id: int) -> list[Project]:
        return (
            self.db.query(Project)
            .options(selectinload(Project.skills).selectinload(ProjectSkill.skill))
            .filter(Project.user_id == user_id)
            .all()
        )

    @staticmethod
    def _eager_load_options():
        return (
            selectinload(DeveloperProfile.user).selectinload(User.skills).selectinload(
                UserSkill.skill
            ),
            selectinload(DeveloperProfile.user)
            .selectinload(User.projects)
            .selectinload(Project.skills)
            .selectinload(ProjectSkill.skill),
        )
