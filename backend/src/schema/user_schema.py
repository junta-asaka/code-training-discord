from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreateRequest(BaseModel):
    name: str
    username: str
    email: EmailStr
    password: str
    description: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    name: str
    username: str
    email: EmailStr
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
