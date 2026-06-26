import uuid
from datetime import datetime

from pydantic import BaseModel


class GoogleLoginRequest(BaseModel):
    id_token: str  # Google OAuth id_token


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}
