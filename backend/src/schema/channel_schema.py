from uuid import UUID

from pydantic import BaseModel, ConfigDict
from schema.message_schema import MessageResponse


class ChannelGetResponse(BaseModel):
    id: UUID
    guild_id: UUID
    name: str
    messages: list[MessageResponse]
    model_config = ConfigDict(from_attributes=True)
