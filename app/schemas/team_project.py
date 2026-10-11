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
    description: str | None = Field(default=None, max_length=5000)
    tech_stack: list[str] = Field(default_factory=list, max_length=30)
    required_skills: list[TeamProjectSkillAdd] = Field(default_factory=list, max_length=30)
    poster_url: str | None = Field(default=None, max_length=500)
    max_members: int = Field(ge=2, le=50)
    college: str | None = Field(default=None, max_length=255)
    college_id: str | None = Field(default=None, max_length=100)
    require_same_college: bool = False

    @model_validator(mode="after")
    def check_college_required(self):
        if self.require_same_college and not (self.college or "").strip() and not (self.college_id or "").strip():
            raise ValueError("college is required when require_same_college is true")
        return self


class TeamProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    tech_stack: list[str] | None = Field(default=None, max_length=30)
    poster_url: str | None = Field(default=None, max_length=500)
    max_members: int | None = Field(default=None, ge=2, le=50)
    college: str | None = Field(default=None, max_length=255)
    college_id: str | None = Field(default=None, max_length=100)
    require_same_college: bool | None = None

    @model_validator(mode="after")
    def check_college_consistency(self):
        if self.require_same_college and self.college is not None and not self.college.strip() and not (self.college_id or "").strip():
            raise ValueError("college is required when require_same_college is true")
        return self


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
    college_id: str | None = None
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
    application_id: int | None = None
    invitation_status: TeamRequestStatus | None = None


class TeamApplicationResponse(BaseModel):
    id: int
    team_project_id: int
    project_title: str | None = None
    user_id: int
    username: str
    full_name: str | None
    message: str | None
    status: TeamRequestStatus
    created_at: datetime
    coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_skills: list[str] = Field(default_factory=list)

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
    message: str | None = Field(default=None, max_length=1000)


class InviteRequest(BaseModel):
    user_id: int
    message: str | None = Field(default=None, max_length=1000)


class SkillEvidence(BaseModel):
    """Proof that a developer really knows a skill: portfolio projects using it."""

    skill: str
    project_titles: list[str] = Field(default_factory=list, max_length=3)
    listed: bool = False  # also an explicitly listed skill (not just project-tagged)


class ProjectRecommendation(BaseModel):
    user_id: int
    username: str
    full_name: str | None
    similarity_score: float
    stars: int = Field(ge=1, le=5)
    skill_overlap: list[str]
    coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    missing_skills: list[str] = Field(default_factory=list)
    bonus_skills: list[str] = Field(default_factory=list, max_length=8)
    skill_evidence: list[SkillEvidence] = Field(default_factory=list)
    application_status: TeamRequestStatus | None = None
    invitation_status: TeamRequestStatus | None = None


class SkillGapEntry(BaseModel):
    skill: str
    covered_by_members: int = 0


class TeamSkillGaps(BaseModel):
    """Which required skills the current team already covers — and what's missing."""

    total_required: int
    covered_skills: list[str] = Field(default_factory=list)
    uncovered_skills: list[str] = Field(default_factory=list)
    coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    by_skill: list[SkillGapEntry] = Field(default_factory=list)


class ProjectRecommendationListResponse(BaseModel):
    recommendations: list[ProjectRecommendation]
    total_candidates: int
