from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class OAuthAccount(Base):
    """Links a local user to a third-party identity (Google/GitHub/LinkedIn).

    A user may connect multiple providers; each provider account maps to
    exactly one local user.
    """

    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint(
            "provider", "provider_user_id", name="uq_oauth_provider_account"
        ),
        UniqueConstraint("provider", "user_id", name="uq_oauth_provider_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="oauth_accounts")
