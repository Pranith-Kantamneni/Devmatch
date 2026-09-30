from pydantic import BaseModel

from app.schemas.profile import PublicProfileResponse
from app.schemas.user import PublicUserResponse


class Recommendation(BaseModel):
    user: PublicUserResponse
    profile: PublicProfileResponse
    similarity_score: float
    skill_overlap: list[str]


class RecommendationListResponse(BaseModel):
    recommendations: list[Recommendation]
    total_candidates: int
