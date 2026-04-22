from fastapi import APIRouter, Depends

from backend.auth.dependencies import get_current_user
from backend.shared.db.models.user import User
from backend.user.schemas import UserResponse

router = APIRouter()


@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
