from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictException,
    InvalidCredentialsException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.models.profile import DeveloperProfile
from app.db.models.refresh_token import RefreshToken
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import RefreshRequest, Token, UserCreate


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

    def authenticate(self, identifier: str, password: str) -> User:
        """Log in with either the email address or the username."""
        cleaned = (identifier or "").strip()
        user = self.user_repo.get_by_email(cleaned)
        if user is None:
            user = self.user_repo.get_by_username(cleaned)
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

    def create_token_pair(self, user: User) -> Token:
        plaintext, digest, expires_at = create_refresh_token()
        # Opportunistic hygiene: drop this user's expired sessions on login.
        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id,
            RefreshToken.expires_at <= datetime.now(timezone.utc).replace(tzinfo=None),
        ).delete()
        self.db.add(
            RefreshToken(user_id=user.id, token_hash=digest, expires_at=expires_at)
        )
        self.db.commit()
        return Token(
            access_token=create_access_token(user.id),
            refresh_token=plaintext,
        )

    def refresh(self, data: RefreshRequest) -> Token:
        """Atomically consume a refresh token and mint a fresh pair.

        Single-statement DELETE..RETURNING makes double-use impossible:
        the first consumer wins, replays find nothing.
        """
        from sqlalchemy import delete

        digest = hash_refresh_token((data.refresh_token or "").strip())
        row = (
            self.db.execute(
                delete(RefreshToken)
                .where(RefreshToken.token_hash == digest)
                .returning(
                    RefreshToken.id,
                    RefreshToken.user_id,
                    RefreshToken.expires_at,
                )
            ).first()
        )
        if row is None:
            raise InvalidCredentialsException(
                "Session expired. Please log in again."
            )
        _, user_id, expires_at = row
        # Column is naive UTC on every backend; compare in the same terms.
        if expires_at is not None:
            if expires_at.tzinfo is not None:
                expires_at = expires_at.replace(tzinfo=None)
            if expires_at <= datetime.now(timezone.utc).replace(tzinfo=None):
                self.db.commit()  # persist the consume
                raise InvalidCredentialsException(
                    "Session expired. Please log in again."
                )
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            self.db.commit()
            raise InvalidCredentialsException("Please log in again.")
        try:
            pair = self.create_token_pair(user)
        except IntegrityError:
            self.db.rollback()
            # Astronomically unlikely token collision — mint once more.
            pair = self.create_token_pair(user)
        self.db.commit()
        return pair

    def logout(self, data: RefreshRequest) -> None:
        digest = hash_refresh_token((data.refresh_token or "").strip())
        row = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.token_hash == digest)
            .first()
        )
        if row is not None:
            self.db.delete(row)
            self.db.commit()
