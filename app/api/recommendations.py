from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user, get_db
from app.db.models.user import User
from app.schemas.recommendation import RecommendationListResponse
from app.services.embedding_service import EmbeddingService
from app.services.matching_service import MatchingService

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get(
    "",
    response_model=RecommendationListResponse,
    summary="Get Top-K developer recommendations for the current user",
)
def get_recommendations(
    limit: int | None = Query(default=None, ge=1, le=100),
    q: str | None = Query(default=None, max_length=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    if limit is None:
        limit = settings.MATCHING_DEFAULT_LIMIT
    limit = min(limit, settings.MATCHING_MAX_LIMIT)

    service = MatchingService(db, settings, EmbeddingService(settings))
    return service.get_recommendations(current_user.id, limit, q=q)
