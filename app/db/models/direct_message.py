from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class DirectConversation(Base):
    """1:1 chat between two users. Starts as a request; messaging unlocks on accept."""

    __tablename__ = "direct_conversations"

    id: Mapped[int] = mapped_column(primary_key=True)

    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    addressee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # "min:max" — one row per unordered pair, enforced unique.
    pair_key: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    requester: Mapped["User"] = relationship(foreign_keys=[requester_id])
    addressee: Mapped["User"] = relationship(foreign_keys=[addressee_id])


class DirectMessage(Base):
    __tablename__ = "direct_messages"
    __table_args__ = (
        Index("ix_direct_messages_convo_created", "conversation_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("direct_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    sender_username: Mapped[str] = mapped_column(
        String(50), nullable=False, default=""
    )

    body: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    conversation: Mapped["DirectConversation"] = relationship()
    sender: Mapped["User | None"] = relationship()
