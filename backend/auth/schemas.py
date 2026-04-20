from backend.shared.models import APIModel


class RegisterRequest(APIModel):
    email: str
    password: str


class LoginRequest(APIModel):
    email: str
    password: str


class RegisterResponse(APIModel):
    user_id: str
    email: str
    access_token: str
    token_type: str = "bearer"


class TokenResponse(APIModel):
    access_token: str
    token_type: str = "bearer"
