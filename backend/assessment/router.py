"""Assessment router - endpoints for cognitive profile assessment.

Three main endpoints:
1. POST /assessment/start - initialize assessment session
1. POST /assessment/submit - submit raw assessment data
3. POST /assessment/complete - finalize assessment session
2. Process asynchronously through normalization → profile → parameters
"""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.assessment.schemas import (
    AssessmentResponse,
    AssessmentSubmission,
    ProfileResponse,
)
from backend.assessment.service import process_assessment, serialize_normalized_signals, serialize_profile_vector
from backend.auth.dependencies import get_current_user
from backend.shared.db.session import get_db_session
from backend.shared.rate_limit import limiter

router = APIRouter(tags=["assessment"])


@router.post("/start", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def start_assessment(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Initialize an assessment session for the authenticated user."""
    return {
        "session_id": str(uuid4()),
        "levels": [1, 2, 3, 4, 5, 6],
        "status": "started",
        "user_id": str(current_user["user"].id),
    }


@router.post("/submit", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def submit_assessment(
    request: Request,
    submission: AssessmentSubmission,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> ProfileResponse:
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
    user_id = current_user["user"].id
    
    # Process assessment through full pipeline
    profile = await process_assessment(
        db_session=db_session,
        user_id=user_id,
        submission=submission,
    )
    
    # Return response with all 6 profile dimensions
    return ProfileResponse(
        profile_id=profile.id or uuid4(),  # In production, retrieve from DB
        user_id=profile.user_id or user_id,
        version=profile.version,
        cognitive_capacity=profile.profile_vector.cognitive_capacity,
        attention_stability=profile.profile_vector.attention_stability,
        learning_tolerance=profile.profile_vector.learning_tolerance,
        motor_baseline=profile.profile_vector.motor_baseline,
        stress_resilience=profile.profile_vector.stress_resilience,
        time_constraint=profile.profile_vector.time_constraint,
    )


@router.post("/complete", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def complete_assessment(
    request: Request,
    payload: dict,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Mark the assessment flow complete and return completion metadata."""
    return {
        "status": "completed",
        "profile_id": str(uuid4()),
        "session_id": payload.get("session_id"),
        "completed_levels": payload.get("completed_levels", []),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "user_id": str(current_user["user"].id),
    }

