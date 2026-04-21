from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.shared.db.models.user import User
from backend.shared.db.session import get_db_session
from backend.cognitive_profile.service import get_cognitive_profile, update_cognitive_profile
from backend.cognitive_profile.schemas import CognitiveProfileResponse, CognitiveProfileUpdate

router = APIRouter()


@router.get("/users/me/cognitive-profile", response_model=CognitiveProfileResponse)
async def get_my_cognitive_profile(
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    return await get_cognitive_profile(db_session, current_user.id)


@router.put("/users/me/cognitive-profile", status_code=status.HTTP_204_NO_CONTENT)
async def update_my_cognitive_profile(
    payload: CognitiveProfileUpdate,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    await update_cognitive_profile(db_session, current_user.id, payload)
