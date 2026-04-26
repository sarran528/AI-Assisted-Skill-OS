"""Assessment schemas for request/response validation."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RawMetrics(BaseModel):
    """Raw behavioral signals from a single assessment level."""
    
    accuracy: float = Field(..., ge=0, le=100, description="Accuracy percentage 0-100")
    expected_time: float = Field(..., ge=0, le=300, description="Expected time in seconds 0-300")
    latency_stability: float = Field(..., ge=0, le=100000, description="Variance in latency 0-100000")
    decay_inverse: float = Field(..., ge=0, le=1, description="Inverse decay 0-1")
    dropout: int = Field(..., ge=0, le=10, description="Dropout attempts 0-10")
    retry: int = Field(..., ge=0, le=10, description="Retry attempts 0-10")
    recovery: float = Field(..., ge=0, le=1, description="Recovery rate 0-1")
    
    # Explicit fields requested by user
    # Explicit fields requested by user (optional for backward compatibility)
    score: int = Field(0, description="Game score/points")
    lives_consumed: int = Field(0, description="Number of lives lost")
    attempts_taken: int = Field(1, description="Total attempts including retries")
    time_taken: float = Field(0.0, description="Total time taken in seconds")


class RawTimeConstraint(BaseModel):
    """Time availability and session preferences."""
    
    available_hours_per_week: float = Field(..., ge=0, le=40, description="Hours available per week 0-40")
    preferred_session_length: float = Field(..., ge=0, le=120, description="Preferred session minutes 0-120")


class AssessmentSubmission(BaseModel):
    """Complete assessment submission for a single level."""
    session_id: UUID | None = Field(default=None, description="Assessment session identifier")
    level: int = Field(..., ge=1, le=6, description="Assessment level 1-6")
    metrics: RawMetrics
    time_constraint: RawTimeConstraint
    score: int = Field(0, ge=0, description="Score earned in this level")


class NormalizedSignals(BaseModel):
    """All 9 normalized signals (0-1 range)."""
    
    n_accuracy: float
    n_latency: float
    n_latency_stability: float
    n_decay_inverse: float
    n_dropout: float
    n_retry: float
    n_recovery: float
    n_hours: float
    n_session_pref: float

    @field_validator("*", mode="before")
    @classmethod
    def validate_normalized(cls, v: float) -> float:
        """Ensure all signals are in [0, 1] range."""
        if not isinstance(v, (int, float)):
            raise ValueError(f"Expected number, got {type(v)}")
        return max(0.0, min(1.0, float(v)))


class ProfileVector(BaseModel):
    """The 6-dimension cognitive profile vector (all 0-1 range)."""
    
    cognitive_capacity: float = Field(..., ge=0, le=1)
    attention_stability: float = Field(..., ge=0, le=1)
    learning_tolerance: float = Field(..., ge=0, le=1)
    motor_baseline: float = Field(..., ge=0, le=1)
    stress_resilience: float = Field(..., ge=0, le=1)
    time_constraint: float = Field(..., ge=0, le=1)


class LearningParameters(BaseModel):
    """All 32 derived learning parameters for a skill."""
    
    # Group A: Difficulty and entry
    difficulty_slope: float
    phase_pacing: float
    entry_phase_offset: float
    repetition_intensity: float
    
    # Group B: Session structure
    session_duration: float
    micro_session_enabled: int  # 0 or 1
    fatigue_threshold: float
    break_frequency: float
    
    # Group C: Technique management
    technique_density: float
    concurrent_technique_limit: int  # 0-5
    abstraction_level: float
    instruction_granularity: float
    
    # Group D: Error handling and checkpoints
    checkpoint_frequency: float
    checkpoint_rigidity: float
    error_tolerance_threshold: float
    retry_limit: int  # 0-5
    
    # Group E: Drill and variation
    drill_depth: float
    variation_intensity: float
    stress_exposure_rate: float
    simulation_complexity: float
    
    # Group F: Feedback
    feedback_detail_level: float
    correction_delay_window: float
    hint_activation_threshold: float
    
    # Group G: Motor/precision
    precision_requirement: float
    speed_requirement: float
    coordination_complexity: float
    
    # Group H: Adaptation and transitions
    adaptation_sensitivity: float
    risk_zone_trigger_level: float
    regression_policy_strength: float
    phase_transition_sensitivity: float
    complexity_escalation_trigger: float
    plateau_detection_threshold: float
    stability_requirement_before_advance: float


class CognitiveProfile(BaseModel):
    """Cognitive profile output for database storage."""
    
    id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    version: int = 1
    profile_vector: ProfileVector
    raw_signals: NormalizedSignals
    created_at: Optional[str] = None


class AssessmentResponse(BaseModel):
    """Response after submitting assessment."""
    
    session_id: UUID
    level: int
    status: str = "in_progress"


class ProfileResponse(BaseModel):
    """Response after completing assessment."""
    
    profile_id: UUID
    user_id: UUID
    version: int
    cognitive_capacity: float
    attention_stability: float
    learning_tolerance: float
    motor_baseline: float
    stress_resilience: float
    time_constraint: float
