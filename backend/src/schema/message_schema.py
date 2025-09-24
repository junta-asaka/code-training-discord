from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MessageCreateRequest(BaseModel):
    channel_id: UUID
    user_id: UUID
    type: str
    content: str
    referenced_message_id: UUID | None
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: UUID
    channel_id: UUID
    user_id: UUID
    type: str
    content: str
    referenced_message_id: UUID | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
