from pydantic import BaseModel, Field


class ParsedSkill(BaseModel):
    name: str
    category: str = "other"
    proficiency: int = Field(default=3, ge=1, le=5)
    years_experience: float = Field(default=1.0, ge=0)


class ParsedExperience(BaseModel):
    title: str | None = None
    company: str | None = None
    duration: str | None = None
    description: str | None = None


class ParsedEducation(BaseModel):
    degree: str | None = None
    institution: str | None = None
    year: str | None = None


class ParsedProject(BaseModel):
    title: str | None = None
    description: str | None = None


class ParsedResume(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    summary: str | None = None
    skills: list[ParsedSkill] = Field(default_factory=list)
    experience: list[ParsedExperience] = Field(default_factory=list)
    education: list[ParsedEducation] = Field(default_factory=list)
    projects: list[ParsedProject] = Field(default_factory=list)
    note: str = (
        "By default, skill level is 3 and experience is 1. Change if required."
    )
