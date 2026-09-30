from sqlalchemy.orm import Session

from app.db.models.project import Project, ProjectSkill
from app.db.models.skill import Skill, UserSkill


class SkillRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: str) -> Skill | None:
        return self.db.query(Skill).filter(Skill.name == name).first()

    def get_or_create_by_name(self, name: str, category) -> Skill:
        skill = self.get_by_name(name)
        if skill is None:
            skill = Skill(name=name, category=category)
            self.db.add(skill)
            self.db.commit()
            self.db.refresh(skill)
        return skill

    def add_user_skill(
        self,
        user_id: int,
        skill_id: int,
        proficiency: int,
        years_experience: float | None,
    ) -> UserSkill:
        user_skill = UserSkill(
            user_id=user_id,
            skill_id=skill_id,
            proficiency=proficiency,
            years_experience=years_experience,
        )
        self.db.add(user_skill)
        self.db.commit()
        self.db.refresh(user_skill)
        return user_skill

    def remove_user_skill(self, user_id: int, skill_id: int) -> bool:
        user_skill = (
            self.db.query(UserSkill)
            .filter(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == skill_id,
            )
            .first()
        )
        if user_skill is None:
            return False
        self.db.delete(user_skill)
        self.db.commit()
        return True

    def create_project(
        self, user_id: int, title: str, description: str | None, url: str | None
    ) -> Project:
        project = Project(
            user_id=user_id,
            title=title,
            description=description,
            url=url,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project(self, project_id: int, user_id: int) -> Project | None:
        return (
            self.db.query(Project)
            .filter(
                Project.id == project_id,
                Project.user_id == user_id,
            )
            .first()
        )

    def add_project_skill(self, project_id: int, skill_id: int) -> ProjectSkill:
        project_skill = ProjectSkill(project_id=project_id, skill_id=skill_id)
        self.db.add(project_skill)
        self.db.commit()
        self.db.refresh(project_skill)
        return project_skill

    def remove_project(self, project_id: int, user_id: int) -> bool:
        project = self.get_project(project_id, user_id)
        if project is None:
            return False
        self.db.delete(project)
        self.db.commit()
        return True
