from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LoginResponse(BaseModel):
    id: UUID
    name: str
    username: str
    access_token: str
    token_type: str = "bearer"
    next: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
