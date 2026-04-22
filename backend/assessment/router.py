"""Assessment router - endpoints for cognitive profile assessment.

Three main endpoints:
1. POST /assessment/start - initialize assessment session
1. POST /assessment/submit - submit raw assessment data
3. POST /assessment/complete - finalize assessment session
2. Process asynchronously through normalization → profile → parameters
"""

from datetime import datetime, timezone
from uuid import UUID
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.assessment.schemas import AssessmentResponse, AssessmentSubmission, ProfileResponse, RawMetrics, RawTimeConstraint
from backend.assessment.service import process_assessment_levels
from backend.auth.dependencies import get_current_user
from backend.shared.db.models import AssessmentSession, CognitiveProfile
from backend.shared.db.session import get_db_session
from backend.shared.rate_limit import limiter

router = APIRouter(tags=["assessment"])


@router.post("/start", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def start_assessment(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Initialize an assessment session for the authenticated user."""
    session_id = uuid4()
    db_session.add(
        AssessmentSession(
            session_id=session_id,
            user_id=current_user["user"].id,
            status="in_progress",
            submissions={},
            completed_levels=[],
        )
    )
    await db_session.commit()
    return {
        "session_id": str(session_id),
        "levels": [1, 2, 3, 4, 5, 6],
        "status": "started",
        "user_id": str(current_user["user"].id),
    }


def _map_level_id(level_id: str | int) -> int:
    mapping = {
        "executive_control": 1,
        "sustained_attention": 2,
        "learning_endurance": 3,
        "motor_precision": 4,
        "pressure_adaptation": 5,
        "time_structuring": 6,
    }
    if isinstance(level_id, int):
        return level_id
    if isinstance(level_id, str) and level_id.isdigit():
        return int(level_id)
    if isinstance(level_id, str) and level_id in mapping:
        return mapping[level_id]
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_level_id")


@router.post("/submit", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def submit_assessment(
    request: Request,
    payload: dict,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> AssessmentResponse:
    """Submit assessment data and compute cognitive profile.
    
    Processes raw behavioral metrics through the complete pipeline:
    1. Normalization to [0, 1] range
    2. Profile vector computation (6 dimensions)
    3. Learning parameter derivation (32 parameters)
    4. Database persistence
    
    Request body:
    {
        "level": 1-6,
        "metrics": {
            "accuracy": 0-100,
            "expected_time": 0-10,
            "latency_stability": 0-25,
            "decay_inverse": 0-1,
            "dropout": 0-10,
            "retry": 0-10,
            "recovery": 0-1
        },
        "time_constraint": {
            "available_hours_per_week": 0-40,
            "preferred_session_length": 0-120
        }
    }
    
    Returns ProfileResponse with computed cognitive profile and all 6 dimensions.
    
    Args:
        request: FastAPI request (for rate limiting).
        submission: Assessment data submission.
        current_user: Authenticated user (from JWT token).
        db_session: Database session.
        
    Returns:
        ProfileResponse with profile_id, user_id, version, and all 6 dimensions.
        
    Raises:
        HTTPException 401: Not authenticated.
        HTTPException 400: Invalid submission data.
        HTTPException 429: Rate limit exceeded.
    """
    if "level_id" in payload:
        level = _map_level_id(payload.get("level_id"))
        raw_metrics = RawMetrics(
            accuracy=float(payload.get("accuracy", 0)) * 100 if float(payload.get("accuracy", 0)) <= 1 else float(payload.get("accuracy", 0)),
            expected_time=float(payload.get("mean_response_time", 0)),
            latency_stability=float(payload.get("response_time_variance", 0)),
            decay_inverse=max(0.0, 1.0 - float(payload.get("performance_decay", 0))),
            dropout=int(payload.get("dropout_depth_index", 0)),
            retry=int(payload.get("retry_depth", 0)),
            recovery=float(payload.get("recovery_slope", 0)),
        )
        time_constraint = RawTimeConstraint(
            available_hours_per_week=float(payload.get("available_hours_per_week", 0)),
            preferred_session_length=float(payload.get("preferred_session_length", 0)),
        )
        submission = AssessmentSubmission(
            session_id=payload.get("session_id"),
            level=level,
            metrics=raw_metrics,
            time_constraint=time_constraint,
        )
    else:
        submission = AssessmentSubmission.model_validate(payload)

    user_id = current_user["user"].id
    session_id = submission.session_id
    session = None

    if session_id is not None:
        session = await db_session.scalar(
            select(AssessmentSession)
            .where(AssessmentSession.session_id == session_id)
            .where(AssessmentSession.user_id == user_id)
        )
    else:
        session = await db_session.scalar(
            select(AssessmentSession)
            .where(AssessmentSession.user_id == user_id)
            .where(AssessmentSession.status == "in_progress")
            .order_by(AssessmentSession.created_at.desc())
        )

    if session is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="assessment_session_required")

    submissions = dict(session.submissions or {})
    submissions[str(submission.level)] = {
        "level": submission.level,
        "metrics": submission.metrics.model_dump(),
        "time_constraint": submission.time_constraint.model_dump(),
    }

    completed_levels = sorted({int(level) for level in submissions.keys()})
    session.submissions = submissions
    session.completed_levels = completed_levels
    session.updated_at = datetime.now(timezone.utc)
    await db_session.commit()

    return AssessmentResponse(
        session_id=session.session_id,
        level=submission.level,
        status="in_progress" if len(completed_levels) < 6 else "ready",
    )


@router.post("/complete", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def complete_assessment(
    request: Request,
    payload: dict,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Finalize an assessment session and compute the profile."""
    session_id = payload.get("session_id")
    if session_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="session_id_required")

    try:
        session_uuid = session_id if isinstance(session_id, UUID) else UUID(session_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_session_id")

    user_id = current_user["user"].id
    session = await db_session.scalar(
        select(AssessmentSession)
        .where(AssessmentSession.session_id == session_uuid)
        .where(AssessmentSession.user_id == user_id)
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="assessment_session_not_found")

    completed_levels = list(session.completed_levels or [])
    if len(completed_levels) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="assessment_incomplete")

    submissions_payload = list((session.submissions or {}).values())
    submissions = [AssessmentSubmission.model_validate(item) for item in submissions_payload]

    profile = await process_assessment_levels(
        db_session=db_session,
        user_id=user_id,
        submissions=submissions,
        session_id=session.session_id,
    )

    session.status = "completed"
    session.updated_at = datetime.now(timezone.utc)
    await db_session.commit()

    return ProfileResponse(
        profile_id=profile.id or uuid4(),
        user_id=profile.user_id or user_id,
        version=profile.version,
        cognitive_capacity=profile.profile_vector.cognitive_capacity,
        attention_stability=profile.profile_vector.attention_stability,
        learning_tolerance=profile.profile_vector.learning_tolerance,
        motor_baseline=profile.profile_vector.motor_baseline,
        stress_resilience=profile.profile_vector.stress_resilience,
        time_constraint=profile.profile_vector.time_constraint,
    )


@router.get("/status")
@limiter.limit("30/minute")
async def assessment_status(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    _ = request
    user_id = current_user["user"].id
    session = await db_session.scalar(
        select(AssessmentSession)
        .where(AssessmentSession.user_id == user_id)
        .order_by(AssessmentSession.created_at.desc())
        .limit(1)
    )
    completed_levels = list(session.completed_levels or []) if session else []
    profile_exists = await db_session.scalar(
        select(CognitiveProfile.id).where(CognitiveProfile.user_id == user_id)
    )
    return {
        "levels_completed": completed_levels,
        "profile_active": profile_exists is not None,
    }

