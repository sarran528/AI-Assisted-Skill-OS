from fastapi import APIRouter, Depends

from backend.auth.dependencies import AuthContext, get_current_user
from backend.auth.schemas import UserResponse

router = APIRouter()


@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: AuthContext = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user.user)
