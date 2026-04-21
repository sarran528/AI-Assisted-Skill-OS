"""Assessment service - orchestrates the complete assessment pipeline.

Handles the flow from raw metrics → normalization → profile vector →
learning parameters, with database persistence and audit logging.

This is the only place in the assessment package that touches the database.
All computations are delegated to pure functions in other modules.
"""

import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.assessment.normalization import normalize_all
from backend.assessment.parameters import compute_learning_parameters
from backend.assessment.profile_vector import compute_profile_vector
from backend.assessment.schemas import (
    AssessmentSubmission,
    CognitiveProfile,
    LearningParameters,
    NormalizedSignals,
    ProfileVector,
)
from backend.shared.audit import log_audit_event
from backend.shared.errors import BusinessError


async def process_assessment(
    db_session: AsyncSession | None,
    user_id: UUID,
    submission: AssessmentSubmission,
) -> CognitiveProfile:
    """Process a complete assessment submission end-to-end.
    
    Pipeline:
    1. Normalize raw signals → [0,1] range
    2. Compute cognitive profile vector (6 dimensions)
    3. Derive 32 learning parameters
    4. Persist to database
    5. Write audit log
    
    Args:
        db_session: Active database session (optional for testing).
        user_id: User performing the assessment.
        submission: Raw assessment data for processing.
        
    Returns:
        CognitiveProfile with all computed values.
        
    Raises:
        BusinessError: If validation or persistence fails.
    """
    try:
        # Step 1: Normalize all signals
        signals = normalize_all(submission.metrics, submission.time_constraint)
        
        # Step 2: Compute profile vector (6 dimensions)
        profile_vector = compute_profile_vector(signals)
        
        # Step 3: Derive 32 learning parameters (not persisted in this basic version)
        # Parameters would be used in skill-specific roadmap generation
        params = compute_learning_parameters(profile_vector, skill_id="generic")
        
        # Step 4: Create profile record for database
        profile = CognitiveProfile(
            user_id=user_id,
            version=1,  # In production, query for max version and increment
            profile_vector=profile_vector,
            raw_signals=signals,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        
        # Step 5: Write audit log (if db_session is available)
        if db_session is not None:
            await log_audit_event(
                db_session=db_session,
                user_id=str(user_id),
                action="assessment_completed",
                entity_type="cognitive_profile",
                entity_id=str(profile.id) if profile.id else None,
                ip_address=None,
                metadata={
                    "level": submission.level,
                    "profile_vector": profile_vector.model_dump(),
                    "signals_normalized": signals.model_dump(),
                },
            )
        
        return profile
        
    except ValueError as e:
        raise BusinessError(f"Assessment processing failed: {str(e)}") from e


def _average_signals(signals: list[NormalizedSignals]) -> NormalizedSignals:
    if not signals:
        raise ValueError("No signals provided for aggregation")

    count = float(len(signals))
    totals: dict[str, float] = {field: 0.0 for field in NormalizedSignals.model_fields}
    for item in signals:
        for field in totals:
            totals[field] += float(getattr(item, field))

    averaged = {field: totals[field] / count for field in totals}
    return NormalizedSignals.model_validate(averaged)


async def process_assessment_levels(
    db_session: AsyncSession | None,
    user_id: UUID,
    submissions: list[AssessmentSubmission],
    session_id: UUID | None = None,
) -> CognitiveProfile:
    """Process multiple assessment submissions into a single profile.

    Aggregates normalized signals across all levels, computes the profile
    vector, and derives learning parameters.
    """
    try:
        normalized = [normalize_all(item.metrics, item.time_constraint) for item in submissions]
        aggregated = _average_signals(normalized)
        profile_vector = compute_profile_vector(aggregated)
        params = compute_learning_parameters(profile_vector, skill_id="generic")

        profile = CognitiveProfile(
            user_id=user_id,
            version=1,
            profile_vector=profile_vector,
            raw_signals=aggregated,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        if db_session is not None:
            await log_audit_event(
                db_session=db_session,
                user_id=str(user_id),
                action="assessment_completed",
                entity_type="cognitive_profile",
                entity_id=str(profile.id) if profile.id else None,
                ip_address=None,
                metadata={
                    "session_id": str(session_id) if session_id else None,
                    "completed_levels": [item.level for item in submissions],
                    "profile_vector": profile_vector.model_dump(),
                    "signals_normalized": aggregated.model_dump(),
                    "learning_parameters": params.model_dump(),
                },
            )

        return profile
    except ValueError as e:
        raise BusinessError(f"Assessment processing failed: {str(e)}") from e


def serialize_profile_vector(vector: ProfileVector) -> dict:
    """Serialize ProfileVector to JSON-compatible dict.
    
    Args:
        vector: ProfileVector instance.
        
    Returns:
        Dict with all 6 dimensions.
    """
    return {
        "cognitive_capacity": float(vector.cognitive_capacity),
        "attention_stability": float(vector.attention_stability),
        "learning_tolerance": float(vector.learning_tolerance),
        "motor_baseline": float(vector.motor_baseline),
        "stress_resilience": float(vector.stress_resilience),
        "time_constraint": float(vector.time_constraint),
    }


def serialize_normalized_signals(signals: NormalizedSignals) -> dict:
    """Serialize NormalizedSignals to JSON-compatible dict.
    
    Args:
        signals: NormalizedSignals instance.
        
    Returns:
        Dict with all 9 signals.
    """
    return {
        "n_accuracy": float(signals.n_accuracy),
        "n_latency": float(signals.n_latency),
        "n_latency_stability": float(signals.n_latency_stability),
        "n_decay_inverse": float(signals.n_decay_inverse),
        "n_dropout": float(signals.n_dropout),
        "n_retry": float(signals.n_retry),
        "n_recovery": float(signals.n_recovery),
        "n_hours": float(signals.n_hours),
        "n_session_pref": float(signals.n_session_pref),
    }
