from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.profiling.schemas import ProfileVectorResponse
from backend.shared.db.models import CognitiveProfile, LearningParameter
from backend.shared.db.session import get_db_session

router = APIRouter()


@router.get("/{user_id}", response_model=ProfileVectorResponse)
async def get_profile(
	user_id: UUID,
	current_user: dict = Depends(get_current_user),
	db_session: AsyncSession = Depends(get_db_session),
) -> ProfileVectorResponse:
	if user_id != current_user["user"].id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

	profile = await db_session.scalar(
		select(CognitiveProfile)
		.where(CognitiveProfile.user_id == user_id)
		.order_by(desc(CognitiveProfile.version))
		.limit(1)
	)
	if profile is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="profile_not_found")

	return ProfileVectorResponse(
		id=profile.id,
		user_id=profile.user_id,
		version=int(profile.version),
		cognitive_capacity=float(profile.cognitive_capacity),
		attention_stability=float(profile.attention_stability),
		learning_tolerance=float(profile.learning_tolerance),
		motor_baseline=float(profile.motor_baseline),
		stress_resilience=float(profile.stress_resilience),
		time_constraint=float(profile.time_constraint),
		raw_signals=profile.raw_signals,
		created_at=profile.created_at,
	)


@router.get("/{user_id}/parameters")
async def get_parameters(
	user_id: UUID,
	current_user: dict = Depends(get_current_user),
	db_session: AsyncSession = Depends(get_db_session),
) -> dict:
	if user_id != current_user["user"].id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

	params = await db_session.scalar(
		select(LearningParameter)
		.join(CognitiveProfile, CognitiveProfile.id == LearningParameter.profile_id)
		.where(CognitiveProfile.user_id == user_id)
		.order_by(desc(CognitiveProfile.version), desc(LearningParameter.created_at))
		.limit(1)
	)
	if params is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="parameters_not_found")

	payload: dict[str, float | int] = {}
	for field in LearningParameter.__table__.columns.keys():
		if field in {"id", "profile_id", "skill_id", "created_at"}:
			continue
		value = getattr(params, field)
		payload[field] = int(value) if isinstance(value, int) else float(value)
	return payload


@router.get("/{user_id}/history", response_model=list[ProfileVectorResponse])
async def get_profile_history(
	user_id: UUID,
	current_user: dict = Depends(get_current_user),
	db_session: AsyncSession = Depends(get_db_session),
) -> list[ProfileVectorResponse]:
	if user_id != current_user["user"].id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

	result = await db_session.execute(
		select(CognitiveProfile)
		.where(CognitiveProfile.user_id == user_id)
		.order_by(desc(CognitiveProfile.version))
	)
	profiles = result.scalars().all()
	return [
		ProfileVectorResponse(
			id=profile.id,
			user_id=profile.user_id,
			version=int(profile.version),
			cognitive_capacity=float(profile.cognitive_capacity),
			attention_stability=float(profile.attention_stability),
			learning_tolerance=float(profile.learning_tolerance),
			motor_baseline=float(profile.motor_baseline),
			stress_resilience=float(profile.stress_resilience),
			time_constraint=float(profile.time_constraint),
			raw_signals=profile.raw_signals,
			created_at=profile.created_at,
		)
		for profile in profiles
	]
