"""Skill grounding probe computation module.

Grounding probes assess user's self-reported ability on three dimensions:
- Recognition: familiarity with skill concepts
- Familiarity: understanding of core ideas via MCQ
- Confidence: self-rating on 1-5 scale

Output is a BaselineSkillState with confidence_bias metric.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.assessment.profile_vector import ProfileVector


PROBE_TYPE_RECOGNITION = "recognition"
PROBE_TYPE_FAMILIARITY = "familiarity"
PROBE_TYPE_CONFIDENCE_ESTIMATION = "confidence_estimation"


@dataclass
class BaselineSkillState:
    """Baseline skill state derived from grounding probes."""
    
    skill_id: str
    user_id: UUID
    exposure_score: float         # 0-1: proportion of recognition items marked familiar
    declarative_score: float      # 0-1: proportion of MCQ answers correct
    confidence_score: float       # 0-1: self-rating normalized (user rates 1-5, divide by 5)
    perceived_level: float        # 0-1: unweighted average of the three scores
    actual_level: float           # 0-1: profile.cognitive_capacity as proxy
    confidence_bias: float        # [-1, 1]: perceived - actual, clamped
    created_at: datetime = None


def _clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp value to range [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def compute_baseline(
    exposure_responses: list[bool],
    familiarity_responses: list[int],
    confidence_response: int,
    profile: ProfileVector,
    skill_id: str,
    user_id: UUID,
) -> BaselineSkillState:
    """Compute baseline skill state from grounding probe responses.
    
    Args:
        exposure_responses: List of booleans, one per recognition item (True = familiar)
        familiarity_responses: List of selected answer indices from MCQ items
        confidence_response: Self-rating from 1 (never tried) to 5 (can teach others)
        profile: User's ProfileVector with cognitive_capacity
        skill_id: ID of skill being grounded
        user_id: ID of user
        
    Returns:
        BaselineSkillState with all scores and confidence_bias
    """
    # Compute exposure_score: proportion of recognition items marked as familiar
    exposure_score = (
        sum(exposure_responses) / len(exposure_responses)
        if exposure_responses else 0.0
    )
    exposure_score = _clamp(exposure_score, 0.0, 1.0)
    
    # Note: We cannot compute declarative_score here without correct answer indices.
    # That computation happens in the service layer with access to the skill template.
    # For now, we'll accept it as a parameter to the parent function.
    
    # Compute confidence_score: normalize 1-5 to 0-1 by dividing by 5
    confidence_score = _clamp(confidence_response / 5.0, 0.0, 1.0)
    
    # Perceived level: unweighted average (will be 3-score average when declarative provided)
    # Placeholder with 2 scores until declarative is computed
    perceived_level_raw = (exposure_score + confidence_score) / 2.0
    
    # Actual level: use cognitive_capacity from profile as proxy
    actual_level = profile.cognitive_capacity
    
    # Confidence bias: perceived - actual, clamped to [-1, 1]
    confidence_bias_raw = perceived_level_raw - actual_level
    confidence_bias = _clamp(confidence_bias_raw, -1.0, 1.0)
    
    return BaselineSkillState(
        skill_id=skill_id,
        user_id=user_id,
        exposure_score=exposure_score,
        declarative_score=0.0,  # Will be computed by service with correct answers
        confidence_score=confidence_score,
        perceived_level=perceived_level_raw,
        actual_level=actual_level,
        confidence_bias=confidence_bias,
        created_at=datetime.now(),
    )


def compute_baseline_with_declarative(
    exposure_responses: list[bool],
    familiarity_responses: list[int],
    familiarity_correct_indices: list[int],
    confidence_response: int,
    profile: ProfileVector,
    skill_id: str,
    user_id: UUID,
) -> BaselineSkillState:
    """Compute baseline skill state with all three probe scores.
    
    Args:
        exposure_responses: List of booleans for recognition items
        familiarity_responses: Selected answer indices from MCQ
        familiarity_correct_indices: Correct answer indices for each MCQ
        confidence_response: Self-rating 1-5
        profile: ProfileVector with cognitive_capacity
        skill_id: Skill ID
        user_id: User ID
        
    Returns:
        BaselineSkillState with all three scores computed
    """
    # Exposure score
    exposure_score = (
        sum(exposure_responses) / len(exposure_responses)
        if exposure_responses else 0.0
    )
    exposure_score = _clamp(exposure_score, 0.0, 1.0)
    
    # Declarative score: proportion of MCQ answers correct
    if familiarity_responses and familiarity_correct_indices:
        correct_count = sum(
            1 for response, correct in zip(familiarity_responses, familiarity_correct_indices)
            if response == correct
        )
        declarative_score = (
            correct_count / len(familiarity_responses)
            if familiarity_responses else 0.0
        )
    else:
        declarative_score = 0.0
    declarative_score = _clamp(declarative_score, 0.0, 1.0)
    
    # Confidence score
    confidence_score = _clamp(confidence_response / 5.0, 0.0, 1.0)
    
    # Perceived level: unweighted average of three scores
    perceived_level = (exposure_score + declarative_score + confidence_score) / 3.0
    perceived_level = _clamp(perceived_level, 0.0, 1.0)
    
    # Actual level
    actual_level = profile.cognitive_capacity
    
    # Confidence bias
    confidence_bias_raw = perceived_level - actual_level
    confidence_bias = _clamp(confidence_bias_raw, -1.0, 1.0)
    
    return BaselineSkillState(
        skill_id=skill_id,
        user_id=user_id,
        exposure_score=exposure_score,
        declarative_score=declarative_score,
        confidence_score=confidence_score,
        perceived_level=perceived_level,
        actual_level=actual_level,
        confidence_bias=confidence_bias,
        created_at=datetime.now(),
    )
