from datetime import datetime

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class TeamMessageResponse(BaseModel):
    id: int
    team_project_id: int
    sender_id: int | None
    sender_username: str
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplicationMessageResponse(TeamMessageResponse):
    application_id: int


# -- direct messages ------------------------------------------------

class ChatRequestCreate(BaseModel):
    user_id: int


class ChatParticipant(BaseModel):
    user_id: int
    username: str


class ConversationResponse(BaseModel):
    id: int
    status: str
    other_user: ChatParticipant
    last_message: TeamMessageResponse | None = None
    updated_at: datetime


class ChatRequestResponse(BaseModel):
    id: int
    status: str
    other_user: ChatParticipant
    created_at: datetime


class ChatOverviewResponse(BaseModel):
    conversations: list[ConversationResponse] = Field(default_factory=list)
    incoming_requests: list[ChatRequestResponse] = Field(default_factory=list)
    outgoing_requests: list[ChatRequestResponse] = Field(default_factory=list)


class ChatStatusResponse(BaseModel):
    status: str  # none | pending_out | pending_in | accepted | rejected
    conversation_id: int | None = None
    request_id: int | None = None


# -- polls ----------------------------------------------------------

class PollCreate(BaseModel):
    question: str = Field(min_length=1, max_length=280)
    options: list[str] = Field(min_length=2, max_length=6)
    allow_multiple: bool = False


class PollVote(BaseModel):
    option_id: int


class PollOptionResponse(BaseModel):
    id: int
    text: str
    votes: int = 0


class PollResponse(BaseModel):
    id: int
    team_project_id: int
    creator_id: int | None
    creator_username: str
    question: str
    is_closed: bool
    allow_multiple: bool = False
    created_at: datetime
    total_votes: int = 0
    options: list[PollOptionResponse] = Field(default_factory=list)
    my_option_id: int | None = None
    my_option_ids: list[int] = Field(default_factory=list)
