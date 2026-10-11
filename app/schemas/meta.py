from pydantic import BaseModel, Field


class CollegeOption(BaseModel):
    id: str
    name: str
    short: str
    city: str
    state: str


class CollegeListResponse(BaseModel):
    colleges: list[CollegeOption] = Field(default_factory=list)
    total: int = 0


class BranchListResponse(BaseModel):
    branches: list[str] = Field(default_factory=list)
    total: int = 0
