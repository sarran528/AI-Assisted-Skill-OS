from datetime import datetime
from typing import Optional

from backend.shared.models import APIModel


class RegisterRequest(APIModel):
    email: str
    password: str


class LoginRequest(APIModel):
    email: str
    password: str


class UserResponse(APIModel):
    id: str
    email: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RegisterResponse(APIModel):
    user_id: str
    email: str
    access_token: str
    token_type: str = "bearer"


class TokenResponse(APIModel):
    access_token: str
    token_type: str = "bearer"
