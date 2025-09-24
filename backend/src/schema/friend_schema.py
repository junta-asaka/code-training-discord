from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FriendCreateRequest(BaseModel):
    username: str
    related_username: str
    # ex) "friend", "block"
    type: str


class FriendCreateResponse(BaseModel):
    id: UUID
    user_id: UUID
    related_user_id: UUID
    type: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class FriendGetResponse(BaseModel):
    name: str
    username: str
    description: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
