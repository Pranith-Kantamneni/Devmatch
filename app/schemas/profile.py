from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.profile import ExperienceLevel
from app.schemas.skill import SkillBrief, UserSkillResponse


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=100)
    bio: str | None = None
    location: str | None = Field(default=None, max_length=100)
    education: str | None = Field(default=None, max_length=255)
    college: str | None = Field(default=None, max_length=255)
    experience_level: ExperienceLevel | None = None
    github_url: str | None = Field(default=None, max_length=255)
    linkedin_url: str | None = Field(default=None, max_length=255)
    portfolio_url: str | None = Field(default=None, max_length=255)
    availability: bool | None = None
    collaboration_preferences: str | None = None


class ProjectAdd(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    url: str | None = Field(default=None, max_length=255)
    skill_names: list[str] = Field(default_factory=list)


class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str | None
    url: str | None
    skills: list[SkillBrief]

    model_config = {"from_attributes": True}


class ProfileResponse(BaseModel):
    user_id: int
    full_name: str | None
    bio: str | None
    location: str | None
    education: str | None
    college: str | None
    experience_level: ExperienceLevel | None
    github_url: str | None
    linkedin_url: str | None
    portfolio_url: str | None
    availability: bool
    collaboration_preferences: str | None
    skills: list[UserSkillResponse]
    projects: list[ProjectResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PublicProfileResponse(BaseModel):
    user_id: int
    full_name: str | None
    bio: str | None
    location: str | None
    education: str | None
    college: str | None
    experience_level: ExperienceLevel | None
    github_url: str | None
    linkedin_url: str | None
    portfolio_url: str | None
    availability: bool
    collaboration_preferences: str | None
    skills: list[UserSkillResponse]
    projects: list[ProjectResponse]

    model_config = {"from_attributes": True}
