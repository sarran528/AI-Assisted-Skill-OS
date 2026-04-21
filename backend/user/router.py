from fastapi import APIRouter, Depends

from backend.auth.dependencies import get_current_user
from backend.auth.schemas import UserResponse
from backend.shared.db.models.user import User

router = APIRouter()


@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
