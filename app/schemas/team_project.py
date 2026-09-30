from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.db.models.skill import SkillCategory
from app.db.models.team_project import TeamRequestStatus
from app.schemas.skill import SkillBrief


class TeamProjectSkillAdd(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: SkillCategory = SkillCategory.OTHER


class TeamProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    tech_stack: list[str] = Field(default_factory=list, max_length=30)
    required_skills: list[TeamProjectSkillAdd] = Field(default_factory=list, max_length=30)
    poster_url: str | None = Field(default=None, max_length=500)
    max_members: int = Field(ge=2, le=50)
    college: str | None = Field(default=None, max_length=255)
    require_same_college: bool = False

    @model_validator(mode="after")
    def check_college_required(self):
        if self.require_same_college and not (self.college or "").strip():
            raise ValueError("college is required when require_same_college is true")
        return self


class TeamProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    tech_stack: list[str] | None = Field(default=None, max_length=30)
    poster_url: str | None = Field(default=None, max_length=500)
    max_members: int | None = Field(default=None, ge=2, le=50)
    college: str | None = Field(default=None, max_length=255)
    require_same_college: bool | None = None


class TeamMemberResponse(BaseModel):
    user_id: int
    username: str
    full_name: str | None
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class TeamProjectResponse(BaseModel):
    id: int
    creator_id: int
    title: str
    description: str | None
    tech_stack: list[str]
    poster_url: str | None
    max_members: int
    member_count: int
    college: str | None
    require_same_college: bool
    required_skills: list[SkillBrief]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TeamProjectDetailResponse(TeamProjectResponse):
    members: list[TeamMemberResponse]
    is_creator: bool = False
    is_member: bool = False
    application_status: TeamRequestStatus | None = None
    invitation_status: TeamRequestStatus | None = None


class TeamApplicationResponse(BaseModel):
    id: int
    team_project_id: int
    user_id: int
    username: str
    full_name: str | None
    message: str | None
    status: TeamRequestStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamInvitationResponse(BaseModel):
    id: int
    team_project_id: int
    project_title: str
    inviter_id: int
    invitee_id: int
    username: str | None = None
    message: str | None
    status: TeamRequestStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplyRequest(BaseModel):
    message: str | None = None


class InviteRequest(BaseModel):
    user_id: int
    message: str | None = None


class ProjectRecommendation(BaseModel):
    user_id: int
    username: str
    full_name: str | None
    similarity_score: float
    skill_overlap: list[str]
    application_status: TeamRequestStatus | None = None
    invitation_status: TeamRequestStatus | None = None


class ProjectRecommendationListResponse(BaseModel):
    recommendations: list[ProjectRecommendation]
    total_candidates: int
