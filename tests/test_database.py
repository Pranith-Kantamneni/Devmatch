import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    DeveloperProfile,
    Project,
    ProjectSkill,
    Skill,
    SkillCategory,
    User,
    UserSkill,
)
from app.repositories.skill_repository import SkillRepository
from app.repositories.user_repository import UserRepository


class TestUserModel:
    def test_create_user(self, db_session):
        user = User(username="alice", email="alice@example.com", password_hash="x")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_unique_username(self, db_session):
        db_session.add(User(username="alice", email="a@example.com", password_hash="x"))
        db_session.commit()
        db_session.add(User(username="alice", email="b@example.com", password_hash="x"))
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_unique_email(self, db_session):
        db_session.add(User(username="alice", email="a@example.com", password_hash="x"))
        db_session.commit()
        db_session.add(User(username="bob", email="a@example.com", password_hash="x"))
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


class TestProfileRelationships:
    def test_user_profile_one_to_one(self, db_session):
        user = User(username="alice", email="a@example.com", password_hash="x")
        db_session.add(user)
        db_session.commit()
        profile = DeveloperProfile(user_id=user.id, full_name="Alice")
        db_session.add(profile)
        db_session.commit()
        assert user.profile.id == profile.id
        assert profile.user.id == user.id

    def test_profile_unique_user_id(self, db_session):
        user = User(username="alice", email="a@example.com", password_hash="x")
        db_session.add(user)
        db_session.commit()
        db_session.add(DeveloperProfile(user_id=user.id))
        db_session.commit()
        db_session.add(DeveloperProfile(user_id=user.id))
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_cascade_delete_profile(self, db_session):
        user = User(username="alice", email="a@example.com", password_hash="x")
        db_session.add(user)
        db_session.commit()
        db_session.add(DeveloperProfile(user_id=user.id))
        db_session.commit()
        db_session.delete(user)
        db_session.commit()
        assert db_session.query(DeveloperProfile).count() == 0


class TestSkillModel:
    def test_get_or_create_skill(self, db_session):
        repo = SkillRepository(db_session)
        skill1 = repo.get_or_create_by_name("python", SkillCategory.LANGUAGE)
        skill2 = repo.get_or_create_by_name("python", SkillCategory.LANGUAGE)
        assert skill1.id == skill2.id

    def test_skill_unique_name(self, db_session):
        db_session.add(Skill(name="python", category=SkillCategory.LANGUAGE))
        db_session.commit()
        db_session.add(Skill(name="python", category=SkillCategory.LANGUAGE))
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_user_skill_unique_constraint(self, db_session):
        user = User(username="alice", email="a@example.com", password_hash="x")
        db_session.add(user)
        db_session.commit()
        skill = Skill(name="python", category=SkillCategory.LANGUAGE)
        db_session.add(skill)
        db_session.commit()
        db_session.add(UserSkill(user_id=user.id, skill_id=skill.id))
        db_session.commit()
        db_session.add(UserSkill(user_id=user.id, skill_id=skill.id))
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_cascade_delete_user_skills(self, db_session):
        user = User(username="alice", email="a@example.com", password_hash="x")
        db_session.add(user)
        db_session.commit()
        skill = Skill(name="python", category=SkillCategory.LANGUAGE)
        db_session.add(skill)
        db_session.commit()
        db_session.add(UserSkill(user_id=user.id, skill_id=skill.id))
        db_session.commit()
        db_session.delete(user)
        db_session.commit()
        assert db_session.query(UserSkill).count() == 0


class TestProjectModel:
    def test_create_project_with_skills(self, db_session):
        user = User(username="alice", email="a@example.com", password_hash="x")
        db_session.add(user)
        db_session.commit()
        skill = Skill(name="python", category=SkillCategory.LANGUAGE)
        db_session.add(skill)
        db_session.commit()
        project = Project(user_id=user.id, title="ML Pipeline")
        db_session.add(project)
        db_session.commit()
        db_session.add(ProjectSkill(project_id=project.id, skill_id=skill.id))
        db_session.commit()
        assert len(project.skills) == 1
        assert project.skills[0].skill.name == "python"

    def test_cascade_delete_project(self, db_session):
        user = User(username="alice", email="a@example.com", password_hash="x")
        db_session.add(user)
        db_session.commit()
        project = Project(user_id=user.id, title="ML Pipeline")
        db_session.add(project)
        db_session.commit()
        db_session.delete(user)
        db_session.commit()
        assert db_session.query(Project).count() == 0

    def test_project_skill_unique_constraint(self, db_session):
        user = User(username="alice", email="a@example.com", password_hash="x")
        db_session.add(user)
        db_session.commit()
        skill = Skill(name="python", category=SkillCategory.LANGUAGE)
        db_session.add(skill)
        db_session.commit()
        project = Project(user_id=user.id, title="ML Pipeline")
        db_session.add(project)
        db_session.commit()
        db_session.add(ProjectSkill(project_id=project.id, skill_id=skill.id))
        db_session.commit()
        db_session.add(ProjectSkill(project_id=project.id, skill_id=skill.id))
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


class TestUserRepository:
    def test_get_by_email(self, db_session):
        repo = UserRepository(db_session)
        db_session.add(User(username="alice", email="a@example.com", password_hash="x"))
        db_session.commit()
        user = repo.get_by_email("a@example.com")
        assert user is not None
        assert user.username == "alice"

    def test_get_by_email_not_found(self, db_session):
        repo = UserRepository(db_session)
        assert repo.get_by_email("nobody@example.com") is None

    def test_list_users_pagination(self, db_session):
        repo = UserRepository(db_session)
        for i in range(5):
            db_session.add(
                User(username=f"user{i}", email=f"u{i}@example.com", password_hash="x")
            )
        db_session.commit()
        users = repo.list_users(skip=1, limit=2)
        assert len(users) == 2
