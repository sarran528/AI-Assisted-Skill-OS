"""Profile vector computation - derives the 6-dimension cognitive profile.

Each dimension is a weighted sum of normalized signals. All output values
are in [0, 1] range, clamped for robustness.

The 6 dimensions represent:
1. cognitive_capacity: Overall information processing ability
2. attention_stability: Sustained focus and consistency
3. learning_tolerance: Ability to handle difficulty and retry
4. motor_baseline: Physical precision and motor control
5. stress_resilience: Performance under pressure and recovery
6. time_constraint: Available time and session preference fit
"""

from backend.assessment.normalization import _clamp
from backend.assessment.schemas import NormalizedSignals, ProfileVector


def compute_profile_vector(signals: NormalizedSignals) -> ProfileVector:
    """Compute the 6-dimension cognitive profile vector.
    
    Each dimension is a weighted sum of the normalized signals.
    All intermediate values and outputs are clamped to [0, 1].
    
    Formulas (all weights sum to 1.0 per dimension):
    
    1. cognitive_capacity = 0.35*accuracy + 0.20*latency + 0.15*latency_stability 
                          + 0.10*decay_inverse + 0.20*recovery
    
    2. attention_stability = 0.50*latency_stability + 0.50*decay_inverse
    
    3. learning_tolerance = 0.40*dropout + 0.40*retry + 0.20*recovery
                          (dropout/retry already inverted: 1-(raw/max))
    
    4. motor_baseline = 0.60*latency + 0.40*latency_stability
    
    5. stress_resilience = 0.60*recovery + 0.40*decay_inverse
    
    6. time_constraint = 0.70*hours + 0.30*session_preference
    
    Args:
        signals: Normalized signal vector with all 9 signals in [0, 1].
        
    Returns:
        ProfileVector with all 6 dimensions in [0, 1].
    """
    
    # Dimension 1: Cognitive Capacity
    # Overall information processing and learning speed ability
    cognitive_capacity = _clamp(
        0.35 * signals.n_accuracy +
        0.20 * signals.n_latency +
        0.15 * signals.n_latency_stability +
        0.10 * signals.n_decay_inverse +
        0.20 * signals.n_recovery
    )
    
    # Dimension 2: Attention Stability
    # Sustained focus and consistency in performance
    attention_stability = _clamp(
        0.50 * signals.n_latency_stability +
        0.50 * signals.n_decay_inverse
    )
    
    # Dimension 3: Learning Tolerance
    # Ability to handle difficulty, retry, and recover from errors
    # Note: n_dropout and n_retry already inverted (1 - raw/max)
    learning_tolerance = _clamp(
        0.40 * signals.n_dropout +
        0.40 * signals.n_retry +
        0.20 * signals.n_recovery
    )
    
    # Dimension 4: Motor Baseline
    # Physical precision, speed, and motor control stability
    motor_baseline = _clamp(
        0.60 * signals.n_latency +
        0.40 * signals.n_latency_stability
    )
    
    # Dimension 5: Stress Resilience
    # Performance under pressure and recovery capability
    stress_resilience = _clamp(
        0.60 * signals.n_recovery +
        0.40 * signals.n_decay_inverse
    )
    
    # Dimension 6: Time Constraint
    # Available study time and session length preferences
    time_constraint = _clamp(
        0.70 * signals.n_hours +
        0.30 * signals.n_session_pref
    )
    
    return ProfileVector(
        cognitive_capacity=cognitive_capacity,
        attention_stability=attention_stability,
        learning_tolerance=learning_tolerance,
        motor_baseline=motor_baseline,
        stress_resilience=stress_resilience,
        time_constraint=time_constraint,
    )
