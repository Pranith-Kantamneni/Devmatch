from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models.direct_message import DirectConversation, DirectMessage


def pair_key(a: int, b: int) -> str:
    return f"{min(a, b)}:{max(a, b)}"


class DirectMessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_pair(self, user_a: int, user_b: int) -> DirectConversation | None:
        return (
            self.db.query(DirectConversation)
            .filter(DirectConversation.pair_key == pair_key(user_a, user_b))
            .first()
        )

    def get_by_id(self, conversation_id: int) -> DirectConversation | None:
        return (
            self.db.query(DirectConversation)
            .filter(DirectConversation.id == conversation_id)
            .first()
        )

    def create_request(self, requester_id: int, addressee_id: int) -> DirectConversation:
        convo = DirectConversation(
            requester_id=requester_id,
            addressee_id=addressee_id,
            pair_key=pair_key(requester_id, addressee_id),
            status="pending",
        )
        self.db.add(convo)
        self.db.commit()
        self.db.refresh(convo)
        return convo

    def set_status(self, convo: DirectConversation, status: str) -> DirectConversation:
        convo.status = status
        self.db.commit()
        self.db.refresh(convo)
        return convo

    def list_for_user(self, user_id: int) -> list[DirectConversation]:
        return (
            self.db.query(DirectConversation)
            .filter(
                or_(
                    DirectConversation.requester_id == user_id,
                    DirectConversation.addressee_id == user_id,
                )
            )
            .order_by(DirectConversation.updated_at.desc())
            .limit(50)
            .all()
        )

    def create_message(
        self, conversation_id: int, sender_id: int | None, sender_username: str, body: str
    ) -> DirectMessage:
        message = DirectMessage(
            conversation_id=conversation_id,
            sender_id=sender_id,
            sender_username=sender_username,
            body=body,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def list_messages(
        self, conversation_id: int, limit: int = 50, before_id: int | None = None
    ) -> list[DirectMessage]:
        query = self.db.query(DirectMessage).filter(
            DirectMessage.conversation_id == conversation_id
        )
        if before_id is not None:
            query = query.filter(DirectMessage.id < before_id)
        rows = query.order_by(DirectMessage.id.desc()).limit(limit).all()
        return list(reversed(rows))

    def last_message(self, conversation_id: int) -> DirectMessage | None:
        return (
            self.db.query(DirectMessage)
            .filter(DirectMessage.conversation_id == conversation_id)
            .order_by(DirectMessage.id.desc())
            .first()
        )
