from typing import Optional

from pydantic import BaseModel


class LoginResponse(BaseModel):
    id: str
    name: str
    username: str
    access_token: str
    token_type: str = "bearer"
    next: Optional[str] = None
