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
from backend.auth.dependencies import AuthContext, get_current_user
from backend.shared.db.models import AssessmentSession, CognitiveProfile, LearningParameter
from backend.shared.db.session import get_db_session
from backend.shared.rate_limit import limiter

router = APIRouter(tags=["assessment"])


@router.post("/start", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def start_assessment(
    request: Request,
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Initialize an assessment session for the authenticated user."""
    session_id = uuid4()
    db_session.add(
        AssessmentSession(
            session_id=session_id,
            user_id=current_user.user.id,
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
        "user_id": str(current_user.user.id),
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


def _normalize_submission_scales(submission: AssessmentSubmission) -> AssessmentSubmission:
    """Normalize mixed frontend metric scales before persistence.

    Some clients send accuracy in [0,1] while schema expects [0,100].
    Convert it once here so DB stores a consistent raw metric format.
    """
    if submission.metrics.accuracy <= 1.0:
        submission.metrics.accuracy = float(submission.metrics.accuracy) * 100.0
    return submission


@router.post("/submit", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def submit_assessment(
    request: Request,
    payload: dict,
    current_user: AuthContext = Depends(get_current_user),
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
            score=int(payload.get("score", 0)),
            lives_consumed=3 - int(payload.get("lives_remaining", 3)),
            attempts_taken=1 + int(payload.get("retry_depth", 0)),
            time_taken=float(payload.get("mean_response_time", 0)),
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
            score=int(payload.get("score", 0)),
        )
    else:
        submission = AssessmentSubmission.model_validate(payload)
    submission = _normalize_submission_scales(submission)

    user_id = current_user.user.id
    session_id = submission.session_id
    session = None

    if session_id is not None:
        session = await db_session.scalar(
            select(AssessmentSession)
            .where(AssessmentSession.session_id == str(session_id))
            .where(AssessmentSession.user_id == str(user_id))
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

    import logging
    logging.info(f"Submitting level {submission.level} for session {session.session_id}")
    
    submissions = dict(session.submissions or {})
    level_key = str(submission.level)
    new_submission = {
        "level": submission.level,
        "metrics": submission.metrics.model_dump(),
        "time_constraint": submission.time_constraint.model_dump(),
        "score": submission.score,
    }
    existing_submission = submissions.get(level_key)
    existing_score = int(existing_submission.get("score", 0)) if isinstance(existing_submission, dict) else 0

    # Keep the best attempt per level so profile generation uses strongest run.
    if existing_submission is None or int(submission.score) >= existing_score:
        submissions[level_key] = new_submission

    # Update cumulative score
    total_score = sum(s.get("score", 0) for s in submissions.values())
    session.score = total_score

    completed_levels = sorted({int(level) for level in submissions.keys()})
    session.submissions = submissions
    session.completed_levels = completed_levels
    session.updated_at = datetime.now(timezone.utc)
    
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(session, "submissions")
    flag_modified(session, "completed_levels")
    
    logging.info(f"Session updated. Levels completed: {completed_levels}. Committing...")
    await db_session.commit()
    logging.info("Commit successful")

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
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Finalize an assessment session and compute the profile."""
    session_id = payload.get("session_id")
    if session_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="session_id_required")

    try:
        session_uuid = session_id if isinstance(session_id, UUID) else UUID(session_id)
        user_id = current_user.user.id
        
        session = await db_session.scalar(
            select(AssessmentSession)
            .where(AssessmentSession.session_id == str(session_uuid))
            .where(AssessmentSession.user_id == str(user_id))
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

        # Fetch parameters for response
        params = await db_session.scalar(
            select(LearningParameter)
            .where(LearningParameter.profile_id == str(profile.id))
            .limit(1)
        )

        return ProfileResponse(
            profile_id=profile.id or uuid4(),
            user_id=profile.user_id or user_id,
            version=profile.version,
            cognitive_capacity=profile.cognitive_capacity,
            attention_stability=profile.attention_stability,
            learning_tolerance=profile.learning_tolerance,
            motor_baseline=profile.motor_baseline,
            stress_resilience=profile.stress_resilience,
            time_constraint=profile.time_constraint,
            learning_parameters=params.__dict__ if params else None
        )

    except (TypeError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"invalid_request: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Error in complete_assessment: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/status")
@limiter.limit("30/minute")
async def assessment_status(
    request: Request,
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    _ = request
    user_id = current_user.user.id
    session = await db_session.scalar(
        select(AssessmentSession)
        .where(AssessmentSession.user_id == user_id)
        .order_by(AssessmentSession.created_at.desc())
        .limit(1)
    )
    completed_levels = list(session.completed_levels or []) if session else []
    profile = await db_session.scalar(
        select(CognitiveProfile)
        .where(CognitiveProfile.user_id == str(user_id))
        .order_by(CognitiveProfile.created_at.desc())
        .limit(1)
    )
    
    params = None
    if profile:
        params = await db_session.scalar(
            select(LearningParameter)
            .where(LearningParameter.profile_id == str(profile.id))
            .limit(1)
        )
    
    return {
        "session_id": str(session.session_id) if session else None,
        "status": session.status if session else "not_started",
        "levels_completed": completed_levels,
        "profile_active": profile is not None,
        "profile_id": str(profile.id) if profile else None,
        "profile": {
            "cognitive_capacity": float(profile.cognitive_capacity),
            "attention_stability": float(profile.attention_stability),
            "learning_tolerance": float(profile.learning_tolerance),
            "motor_baseline": float(profile.motor_baseline),
            "stress_resilience": float(profile.stress_resilience),
            "time_constraint": float(profile.time_constraint),
        } if profile else None,
        "learning_parameters": params.__dict__ if params else None
    }

