from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> User | None:
        return (
            self.db.query(User)
            .filter(func.lower(User.email) == (email or "").strip().lower())
            .first()
        )

    def get_by_username(self, username: str) -> User | None:
        return (
            self.db.query(User)
            .filter(func.lower(User.username) == (username or "").strip().lower())
            .first()
        )

    def get_by_email_or_username(self, email: str, username: str) -> User | None:
        return self.db.query(User).filter(
            (func.lower(User.email) == (email or "").strip().lower())
            | (func.lower(User.username) == (username or "").strip().lower())
        ).first()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        return self.db.query(User).order_by(User.id).offset(skip).limit(limit).all()

    def count_users(self) -> int:
        return self.db.query(User).count()
