from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, InvalidCredentialsException
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
        existing = self.user_repo.get_by_email_or_username(
            user_data.email, user_data.username
        )
        if existing:
            raise ConflictException("Username or email already exists")

        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
        )
        user = self.user_repo.create(user)

        self.db.add(DeveloperProfile(user_id=user.id))
        self.db.commit()

        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.user_repo.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsException("Invalid email or password")
        return user

    def create_token(self, user: User) -> Token:
        return Token(access_token=create_access_token(user.id))
