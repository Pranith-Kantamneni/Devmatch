from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import PublicUserResponse, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/",
    response_model=list[PublicUserResponse],
    summary="List users (public information)",
)
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    return repo.list_users(skip=skip, limit=limit)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current authenticated user",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user
