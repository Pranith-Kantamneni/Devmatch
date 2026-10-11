from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictException,
    InvalidCredentialsException,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.profile import DeveloperProfile
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import Token, UserCreate


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register(self, user_data: UserCreate) -> User:
        email = user_data.email.strip().lower()
        username = user_data.username.strip()
        existing = self.user_repo.get_by_email_or_username(email, username)
        if existing:
            raise ConflictException("Username or email already exists")

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(user_data.password),
        )
        try:
            user = self.user_repo.create(user)
        except IntegrityError:
            self.db.rollback()
            raise ConflictException("Username or email already exists")

        try:
            self.db.add(DeveloperProfile(user_id=user.id))
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            # User row already exists; a concurrent request may have created
            # the profile — treat as conflict-free and return the user.
            pass

        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.user_repo.get_by_email(email)
        if user is None:
            raise InvalidCredentialsException("Invalid email or password")
        if not user.password_hash:
            # Signed up via Google/GitHub/LinkedIn — no password set.
            raise InvalidCredentialsException(
                "This account uses social login. Please sign in with your provider."
            )
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsException("Invalid email or password")
        return user

    def create_token(self, user: User) -> Token:
        return Token(access_token=create_access_token(user.id))
