"""1:1 chat: request → accept/decline → message."""

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.db.models.direct_message import DirectConversation
from app.repositories.dm_repository import DirectMessageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.chat import (
    ChatOverviewResponse,
    ChatParticipant,
    ChatRequestResponse,
    ChatStatusResponse,
    ConversationResponse,
    TeamMessageResponse,
)


class DirectMessageService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DirectMessageRepository(db)
        self.user_repo = UserRepository(db)

    # -- requests ----------------------------------------------------

    def request_chat(self, requester_id: int, target_id: int) -> ChatRequestResponse:
        if requester_id == target_id:
            raise ValidationException("You cannot chat with yourself")
        target = self.user_repo.get_by_id(target_id)
        if target is None:
            raise NotFoundException("User not found")

        existing = self.repo.get_pair(requester_id, target_id)
        if existing is not None:
            if existing.status == "pending":
                raise ConflictException("Chat request already pending")
            if existing.status == "accepted":
                raise ConflictException("You already have a chat with this user")
            # Rejected before — reopen the same thread as a fresh request.
            self.repo.set_status(existing, "pending")
            return self._to_request_response(existing, requester_id)

        convo = self.repo.create_request(requester_id, target_id)
        return self._to_request_response(convo, requester_id)

    def respond_to_request(
        self, requester_id: int, conversation_id: int, accept: bool
    ) -> ChatRequestResponse:
        convo = self._get_or_404(conversation_id)
        if convo.addressee_id != requester_id:
            raise ForbiddenException("Only the invited user can respond")
        if convo.status != "pending":
            raise ValidationException("This request is no longer pending")
        self.repo.set_status(convo, "accepted" if accept else "rejected")
        return self._to_request_response(convo, requester_id)

    def status_with(self, requester_id: int, target_id: int) -> ChatStatusResponse:
        if requester_id == target_id:
            return ChatStatusResponse(status="none")
        existing = self.repo.get_pair(requester_id, target_id)
        if existing is None:
            return ChatStatusResponse(status="none")
        if existing.status == "accepted":
            return ChatStatusResponse(status="accepted", conversation_id=existing.id)
        if existing.status == "pending":
            if existing.requester_id == requester_id:
                return ChatStatusResponse(
                    status="pending_out", request_id=existing.id
                )
            return ChatStatusResponse(status="pending_in", request_id=existing.id)
        return ChatStatusResponse(status="rejected")

    def overview(self, user_id: int) -> ChatOverviewResponse:
        conversations: list[ConversationResponse] = []
        incoming: list[ChatRequestResponse] = []
        outgoing: list[ChatRequestResponse] = []
        for convo in self.repo.list_for_user(user_id):
            if convo.status == "accepted":
                conversations.append(self._to_conversation_response(convo, user_id))
            elif convo.status == "pending":
                if convo.addressee_id == user_id:
                    incoming.append(self._to_request_response(convo, user_id))
                else:
                    outgoing.append(self._to_request_response(convo, user_id))
        return ChatOverviewResponse(
            conversations=conversations,
            incoming_requests=incoming,
            outgoing_requests=outgoing,
        )

    # -- messages ----------------------------------------------------

    def _require_participant(
        self, user_id: int, conversation_id: int
    ) -> DirectConversation:
        convo = self._get_or_404(conversation_id)
        if user_id not in (convo.requester_id, convo.addressee_id):
            raise ForbiddenException("You are not part of this chat")
        if convo.status != "accepted":
            raise ForbiddenException("Chat unlocks once the request is accepted")
        return convo

    def list_messages(
        self, user_id: int, conversation_id: int, limit: int, before_id: int | None
    ) -> list[TeamMessageResponse]:
        self._require_participant(user_id, conversation_id)
        return [
            self._to_message_response(m)
            for m in self.repo.list_messages(conversation_id, limit, before_id)
        ]

    def post_message(
        self, user_id: int, conversation_id: int, body: str
    ) -> TeamMessageResponse:
        self._require_participant(user_id, conversation_id)
        cleaned = (body or "").strip()
        if not cleaned:
            raise ValidationException("Message must not be empty")
        if len(cleaned) > 2000:
            raise ValidationException("Message is too long (max 2000 characters)")
        sender = self.user_repo.get_by_id(user_id)
        message = self.repo.create_message(
            conversation_id,
            user_id,
            sender.username if sender else "Someone",
            cleaned,
        )
        return self._to_message_response(message)

    # -- helpers -----------------------------------------------------

    def _get_or_404(self, conversation_id: int) -> DirectConversation:
        convo = self.repo.get_by_id(conversation_id)
        if convo is None:
            raise NotFoundException("Chat not found")
        return convo

    def _other(self, convo: DirectConversation, user_id: int) -> ChatParticipant:
        other_id = (
            convo.addressee_id if convo.requester_id == user_id else convo.requester_id
        )
        other = self.user_repo.get_by_id(other_id)
        return ChatParticipant(
            user_id=other_id, username=other.username if other else "Someone"
        )

    def _to_request_response(
        self, convo: DirectConversation, user_id: int
    ) -> ChatRequestResponse:
        return ChatRequestResponse(
            id=convo.id,
            status=convo.status,
            other_user=self._other(convo, user_id),
            created_at=convo.created_at,
        )

    def _to_conversation_response(
        self, convo: DirectConversation, user_id: int
    ) -> ConversationResponse:
        last = self.repo.last_message(convo.id)
        return ConversationResponse(
            id=convo.id,
            status=convo.status,
            other_user=self._other(convo, user_id),
            last_message=self._to_message_response(last) if last else None,
            updated_at=convo.updated_at,
        )

    @staticmethod
    def _to_message_response(message) -> TeamMessageResponse:
        return TeamMessageResponse(
            id=message.id,
            team_project_id=0,
            sender_id=message.sender_id,
            sender_username=message.sender_username or "Someone",
            body=message.body,
            created_at=message.created_at,
        )
