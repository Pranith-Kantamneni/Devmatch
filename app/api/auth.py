from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.user import RefreshRequest, Token, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.register(user_data)


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate with email or username, receive tokens",
)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.authenticate(user_data.email, user_data.password)
    return service.create_token_pair(user)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Rotate a refresh token into a fresh token pair",
)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    return AuthService(db).refresh(data)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a refresh token",
)
def logout(data: RefreshRequest, db: Session = Depends(get_db)):
    AuthService(db).logout(data)
    return None
