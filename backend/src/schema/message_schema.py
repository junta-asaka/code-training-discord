from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    id: UUID
    channel_id: UUID
    user_id: UUID
    type: str
    content: str
    referenced_message_id: UUID | None
    created_at: str
    updated_at: str
    model_config = ConfigDict(from_attributes=True)
