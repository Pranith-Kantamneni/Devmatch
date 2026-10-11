from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.models.user import User
from app.db.session import get_db

security = HTTPBearer(auto_error=False)


def _auth_error(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise _auth_error("Not authenticated")

    user_id = decode_access_token(credentials.credentials)

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise _auth_error("User not found")

    return user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None

    # An explicitly provided but invalid/expired token must not silently
    # degrade to an anonymous view — surface 401 so clients can re-login.
    user_id = decode_access_token(credentials.credentials)

    return db.query(User).filter(User.id == user_id).first()
