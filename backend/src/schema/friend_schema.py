from typing import Optional

from pydantic import BaseModel


class FriendCreateRequest(BaseModel):
    username: str
    related_username: str
    # ex) "friend", "block"
    type: str


class FriendCreateResponse(BaseModel):
    id: str
    user_id: str
    related_user_id: str
    type: str
    created_at: str


class FriendGetResponse(BaseModel):
    name: str
    username: str
    description: Optional[str] = None
    created_at: str
