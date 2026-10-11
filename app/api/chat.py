from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db.models.user import User
from app.schemas.chat import (
    ChatOverviewResponse,
    ChatRequestCreate,
    ChatRequestResponse,
    ChatStatusResponse,
    MessageCreate,
    TeamMessageResponse,
)
from app.services.dm_service import DirectMessageService

router = APIRouter(prefix="/chat", tags=["Direct Messages"])


def get_dm_service(db: Session = Depends(get_db)) -> DirectMessageService:
    return DirectMessageService(db)


@router.get(
    "/overview",
    response_model=ChatOverviewResponse,
    summary="My chats, incoming requests, and outgoing requests",
)
def chat_overview(
    current_user: User = Depends(get_current_user),
    service: DirectMessageService = Depends(get_dm_service),
):
    return service.overview(current_user.id)


@router.get(
    "/with/{user_id}",
    response_model=ChatStatusResponse,
    summary="Chat status with another user",
)
def chat_status(
    user_id: int,
    current_user: User = Depends(get_current_user),
    service: DirectMessageService = Depends(get_dm_service),
):
    return service.status_with(current_user.id, user_id)


@router.post(
    "/requests",
    response_model=ChatRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request a 1:1 chat with another user",
)
def request_chat(
    data: ChatRequestCreate,
    current_user: User = Depends(get_current_user),
    service: DirectMessageService = Depends(get_dm_service),
):
    return service.request_chat(current_user.id, data.user_id)


@router.post(
    "/requests/{conversation_id}/accept",
    response_model=ChatRequestResponse,
    summary="Accept a chat request",
)
def accept_chat(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    service: DirectMessageService = Depends(get_dm_service),
):
    return service.respond_to_request(current_user.id, conversation_id, accept=True)


@router.post(
    "/requests/{conversation_id}/reject",
    response_model=ChatRequestResponse,
    summary="Decline a chat request",
)
def reject_chat(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    service: DirectMessageService = Depends(get_dm_service),
):
    return service.respond_to_request(current_user.id, conversation_id, accept=False)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[TeamMessageResponse],
    summary="Read a 1:1 chat thread",
)
def list_dm_messages(
    conversation_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    before_id: int | None = Query(default=None, ge=1),
    current_user: User = Depends(get_current_user),
    service: DirectMessageService = Depends(get_dm_service),
):
    return service.list_messages(current_user.id, conversation_id, limit, before_id)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=TeamMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a 1:1 chat message",
)
def post_dm_message(
    conversation_id: int,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    service: DirectMessageService = Depends(get_dm_service),
):
    return service.post_message(current_user.id, conversation_id, data.body)
