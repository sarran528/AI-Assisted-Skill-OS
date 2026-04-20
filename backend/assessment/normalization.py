"""Assessment signal normalization - converts raw metrics to [0,1] range.

All normalization functions produce values in [0, 1]. Clamping is applied
to handle edge cases and ensure the output never exceeds the valid range.

Critical: The dropout and retry metrics use inverted formulas:
- normalize_dropout: Higher dropout attempts → lower score (1 - inverted)
- normalize_retry: Higher retry attempts → lower score (1 - inverted)
These inversions match the schema document exactly.
"""

from typing import TypedDict

from backend.assessment.schemas import NormalizedSignals, RawMetrics, RawTimeConstraint


# Constants for normalization bounds
MAX_ACCURACY = 100.0
MAX_EXPECTED_TIME = 10.0
MAX_VARIANCE = 25.0
MAX_DECAY_INVERSE = 1.0
MAX_DROPOUT = 10.0
MAX_RETRY = 10.0
MAX_RECOVERY = 1.0
MAX_HOURS = 40.0
MAX_SESSION_LENGTH = 120.0


def _clamp(value: float) -> float:
    """Clamp value to [0, 1] range.
    
    Args:
        value: Input value to clamp.
        
    Returns:
        Value clamped to [0, 1].
    """
    return max(0.0, min(1.0, value))


def normalize_accuracy(raw_accuracy: float) -> float:
    """Normalize accuracy percentage to [0, 1].
    
    Formula: accuracy / 100
    
    Args:
        raw_accuracy: Raw accuracy 0-100%.
        
    Returns:
        Normalized accuracy 0-1.
    """
    result = raw_accuracy / MAX_ACCURACY
    return _clamp(result)


def normalize_latency(expected_time: float) -> float:
    """Normalize latency (lower time is better).
    
    Formula: 1 - (time / 10)
    Inversion: faster execution → higher score.
    
    Args:
        expected_time: Raw latency 0-10 seconds.
        
    Returns:
        Normalized latency 0-1.
    """
    result = 1.0 - (expected_time / MAX_EXPECTED_TIME)
    return _clamp(result)


def normalize_latency_stability(variance: float) -> float:
    """Normalize latency stability (lower variance is better).
    
    Formula: 1 - (variance / 25)
    Inversion: lower variance → higher score.
    
    Args:
        variance: Raw variance 0-25.
        
    Returns:
        Normalized stability 0-1.
    """
    result = 1.0 - (variance / MAX_VARIANCE)
    return _clamp(result)


def normalize_decay_inverse(decay_inverse: float) -> float:
    """Normalize decay inverse (already normalized).
    
    Formula: decay_inverse (pass-through)
    Range: 0-1 directly.
    
    Args:
        decay_inverse: Raw decay inverse 0-1.
        
    Returns:
        Normalized decay inverse 0-1.
    """
    result = decay_inverse / MAX_DECAY_INVERSE
    return _clamp(result)


def normalize_dropout(dropout_attempts: int) -> float:
    """Normalize dropout attempts (lower attempts is better).
    
    Formula: 1 - (dropout / 10)
    Inversion: fewer dropouts → higher score.
    Critical: This uses inverted logic.
    
    Args:
        dropout_attempts: Raw dropout count 0-10.
        
    Returns:
        Normalized dropout 0-1 (inverted).
    """
    result = 1.0 - (dropout_attempts / MAX_DROPOUT)
    return _clamp(result)


def normalize_retry(retry_attempts: int) -> float:
    """Normalize retry attempts (lower attempts is better).
    
    Formula: 1 - (retry / 10)
    Inversion: fewer retries → higher score.
    Critical: This uses inverted logic.
    
    Args:
        retry_attempts: Raw retry count 0-10.
        
    Returns:
        Normalized retry 0-1 (inverted).
    """
    result = 1.0 - (retry_attempts / MAX_RETRY)
    return _clamp(result)


def normalize_recovery(recovery_rate: float) -> float:
    """Normalize recovery rate (pass-through).
    
    Formula: recovery / 1.0
    Range: 0-1 directly (already normalized).
    
    Args:
        recovery_rate: Raw recovery rate 0-1.
        
    Returns:
        Normalized recovery 0-1.
    """
    result = recovery_rate / MAX_RECOVERY
    return _clamp(result)


def normalize_hours(available_hours: float) -> float:
    """Normalize available hours per week.
    
    Formula: hours / 40
    
    Args:
        available_hours: Available hours per week 0-40.
        
    Returns:
        Normalized hours 0-1.
    """
    result = available_hours / MAX_HOURS
    return _clamp(result)


def normalize_session_preference(session_length: float) -> float:
    """Normalize preferred session length in minutes.
    
    Formula: session_length / 120
    
    Args:
        session_length: Preferred session minutes 0-120.
        
    Returns:
        Normalized session preference 0-1.
    """
    result = session_length / MAX_SESSION_LENGTH
    return _clamp(result)


def normalize_all(
    metrics: RawMetrics,
    time_constraint: RawTimeConstraint,
) -> NormalizedSignals:
    """Normalize all 9 signals from raw assessment data.
    
    Applies all individual normalizers and returns the complete
    normalized signal vector. All values are guaranteed in [0, 1].
    
    Args:
        metrics: Raw behavioral metrics.
        time_constraint: Time availability constraints.
        
    Returns:
        NormalizedSignals with all 9 signals in [0, 1].
    """
    return NormalizedSignals(
        n_accuracy=normalize_accuracy(metrics.accuracy),
        n_latency=normalize_latency(metrics.expected_time),
        n_latency_stability=normalize_latency_stability(metrics.latency_stability),
        n_decay_inverse=normalize_decay_inverse(metrics.decay_inverse),
        n_dropout=normalize_dropout(metrics.dropout),
        n_retry=normalize_retry(metrics.retry),
        n_recovery=normalize_recovery(metrics.recovery),
        n_hours=normalize_hours(time_constraint.available_hours_per_week),
        n_session_pref=normalize_session_preference(time_constraint.preferred_session_length),
    )
