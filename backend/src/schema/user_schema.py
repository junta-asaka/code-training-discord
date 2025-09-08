from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreateRequest(BaseModel):
    name: str
    username: str
    email: EmailStr
    password: str
    description: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    name: str
    username: str
    email: EmailStr
    description: Optional[str] = None
    created_at: str
    updated_at: str
