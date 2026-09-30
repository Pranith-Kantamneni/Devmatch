from pydantic import BaseModel, Field

from app.db.models.skill import SkillCategory


class SkillAdd(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: SkillCategory = SkillCategory.OTHER
    proficiency: int = Field(default=3, ge=1, le=5)
    years_experience: float | None = Field(default=None, ge=0)


class SkillBrief(BaseModel):
    id: int
    name: str
    category: SkillCategory

    model_config = {"from_attributes": True}


class UserSkillResponse(BaseModel):
    skill_id: int
    name: str
    category: SkillCategory
    proficiency: int
    years_experience: float | None

    model_config = {"from_attributes": True}
