"""Tests for assessment normalization functions.

Comprehensive tests for all 9 normalization functions, covering:
- Boundary values (0, max, midpoint)
- Clamping on out-of-range inputs
- Inverted formula verification (dropout, retry)
"""

import pytest

from backend.assessment.normalization import (
    MAX_ACCURACY,
    MAX_DROPOUT,
    MAX_EXPECTED_TIME,
    MAX_RECOVERY,
    MAX_RETRY,
    MAX_SESSION_LENGTH,
    MAX_VARIANCE,
    MAX_HOURS,
    MAX_DECAY_INVERSE,
    normalize_accuracy,
    normalize_decay_inverse,
    normalize_dropout,
    normalize_hours,
    normalize_latency,
    normalize_latency_stability,
    normalize_recovery,
    normalize_retry,
    normalize_session_preference,
)


class TestNormalizeAccuracy:
    """Tests for accuracy normalization: value / 100."""
    
    def test_zero_accuracy(self):
        """Zero accuracy maps to 0."""
        assert normalize_accuracy(0.0) == 0.0
    
    def test_max_accuracy(self):
        """100% accuracy maps to 1.0."""
        assert normalize_accuracy(MAX_ACCURACY) == 1.0
    
    def test_midpoint_accuracy(self):
        """50% accuracy maps to 0.5."""
        assert normalize_accuracy(50.0) == 0.5
    
    def test_over_range_clamped(self):
        """Values above 100 clamp to 1.0."""
        assert normalize_accuracy(150.0) == 1.0
    
    def test_negative_clamped(self):
        """Negative values clamp to 0.0."""
        assert normalize_accuracy(-10.0) == 0.0


class TestNormalizeLatency:
    """Tests for latency normalization: 1 - (time / 10). Lower time is better."""
    
    def test_zero_latency(self):
        """Zero latency (fastest) maps to 1.0."""
        assert normalize_latency(0.0) == 1.0
    
    def test_max_latency(self):
        """10s latency (maximum) maps to 0.0."""
        assert normalize_latency(MAX_EXPECTED_TIME) == 0.0
    
    def test_midpoint_latency(self):
        """5s latency maps to 0.5."""
        assert normalize_latency(5.0) == 0.5
    
    def test_over_range_clamped(self):
        """Values above max clamp to 0.0."""
        assert normalize_latency(20.0) == 0.0
    
    def test_negative_clamped(self):
        """Negative latency clamps to 1.0."""
        assert normalize_latency(-1.0) == 1.0


class TestNormalizeLatencyStability:
    """Tests for latency stability: 1 - (variance / 25). Lower variance is better."""
    
    def test_zero_variance(self):
        """Zero variance (perfect consistency) maps to 1.0."""
        assert normalize_latency_stability(0.0) == 1.0
    
    def test_max_variance(self):
        """25 variance (maximum) maps to 0.0."""
        assert normalize_latency_stability(MAX_VARIANCE) == 0.0
    
    def test_midpoint_variance(self):
        """12.5 variance maps to 0.5."""
        assert normalize_latency_stability(12.5) == 0.5
    
    def test_over_range_clamped(self):
        """Variance above 25 clamps to 0.0."""
        assert normalize_latency_stability(50.0) == 0.0


class TestNormalizeDecayInverse:
    """Tests for decay inverse: pass-through (already 0-1)."""
    
    def test_zero(self):
        """0 maps to 0."""
        assert normalize_decay_inverse(0.0) == 0.0
    
    def test_one(self):
        """1 maps to 1."""
        assert normalize_decay_inverse(1.0) == 1.0
    
    def test_midpoint(self):
        """0.5 maps to 0.5."""
        assert normalize_decay_inverse(0.5) == 0.5


class TestNormalizeDropout:
    """Tests for dropout (inverted): 1 - (attempts / 10).
    
    Fewer dropout attempts → higher score (inverted logic).
    Critical regression test: these inversions have been misimplemented before.
    """
    
    def test_zero_dropout(self):
        """Zero dropout attempts maps to 1.0 (perfect)."""
        assert normalize_dropout(0) == 1.0
    
    def test_max_dropout(self):
        """10 dropout attempts maps to 0.0."""
        assert normalize_dropout(10) == 0.0
    
    def test_midpoint_dropout(self):
        """5 dropout attempts maps to 0.5."""
        assert normalize_dropout(5) == 0.5
    
    def test_inverted_boundary_low(self):
        """Verify inversion: low attempts are good."""
        assert normalize_dropout(0) > normalize_dropout(5)
    
    def test_inverted_boundary_high(self):
        """Verify inversion: high attempts are bad."""
        assert normalize_dropout(5) > normalize_dropout(10)
    
    def test_over_range_clamped(self):
        """Attempts above 10 clamp to 0.0."""
        assert normalize_dropout(15) == 0.0


class TestNormalizeRetry:
    """Tests for retry (inverted): 1 - (attempts / 10).
    
    Fewer retry attempts → higher score (inverted logic).
    Critical regression test: same as dropout inversion.
    """
    
    def test_zero_retry(self):
        """Zero retry attempts maps to 1.0 (perfect)."""
        assert normalize_retry(0) == 1.0
    
    def test_max_retry(self):
        """10 retry attempts maps to 0.0."""
        assert normalize_retry(10) == 0.0
    
    def test_midpoint_retry(self):
        """5 retry attempts maps to 0.5."""
        assert normalize_retry(5) == 0.5
    
    def test_inverted_boundary_low(self):
        """Verify inversion: low attempts are good."""
        assert normalize_retry(0) > normalize_retry(5)
    
    def test_inverted_boundary_high(self):
        """Verify inversion: high attempts are bad."""
        assert normalize_retry(5) > normalize_retry(10)
    
    def test_over_range_clamped(self):
        """Attempts above 10 clamp to 0.0."""
        assert normalize_retry(15) == 0.0


class TestNormalizeRecovery:
    """Tests for recovery rate: pass-through (already 0-1)."""
    
    def test_zero_recovery(self):
        """0 recovery maps to 0."""
        assert normalize_recovery(0.0) == 0.0
    
    def test_full_recovery(self):
        """1.0 recovery maps to 1.0."""
        assert normalize_recovery(1.0) == 1.0
    
    def test_midpoint_recovery(self):
        """0.5 recovery maps to 0.5."""
        assert normalize_recovery(0.5) == 0.5


class TestNormalizeHours:
    """Tests for available hours per week: hours / 40."""
    
    def test_zero_hours(self):
        """Zero hours maps to 0."""
        assert normalize_hours(0.0) == 0.0
    
    def test_max_hours(self):
        """40 hours maps to 1.0."""
        assert normalize_hours(MAX_HOURS) == 1.0
    
    def test_midpoint_hours(self):
        """20 hours maps to 0.5."""
        assert normalize_hours(20.0) == 0.5
    
    def test_over_range_clamped(self):
        """Hours above 40 clamp to 1.0."""
        assert normalize_hours(80.0) == 1.0


class TestNormalizeSessionPreference:
    """Tests for preferred session length: length / 120."""
    
    def test_zero_session(self):
        """Zero minutes maps to 0."""
        assert normalize_session_preference(0.0) == 0.0
    
    def test_max_session(self):
        """120 minutes maps to 1.0."""
        assert normalize_session_preference(MAX_SESSION_LENGTH) == 1.0
    
    def test_midpoint_session(self):
        """60 minutes maps to 0.5."""
        assert normalize_session_preference(60.0) == 0.5
    
    def test_over_range_clamped(self):
        """Length above 120 clamps to 1.0."""
        assert normalize_session_preference(240.0) == 1.0


class TestClampingRobustness:
    """Test clamping behavior across all functions."""
    
    def test_negative_values_clamp_to_zero(self):
        """All normalization functions clamp negative inputs to 0."""
        assert normalize_accuracy(-50) == 0.0
        assert normalize_latency(-5) >= 0.0  # May map to high value, then clamp
        assert normalize_dropout(-1) >= 0.0
    
    def test_extreme_positive_values_clamp(self):
        """All normalization functions clamp extreme positive inputs."""
        assert normalize_accuracy(1000) == 1.0
        assert normalize_hours(1000) == 1.0
        assert normalize_dropout(100) == 0.0


class TestInversionConsistency:
    """Verify that inverted formulas behave consistently."""
    
    def test_dropout_and_retry_both_inverted(self):
        """Both dropout and retry use same inversion pattern."""
        for i in range(11):
            d_norm = normalize_dropout(i)
            r_norm = normalize_retry(i)
            assert d_norm == r_norm, f"Inversion mismatch at {i}"
    
    def test_latency_variants_inverted(self):
        """Latency and stability both use 1 - formula (inverted)."""
        # Lower latency should be better
        assert normalize_latency(2.0) > normalize_latency(8.0)
        # Lower variance should be better
        assert normalize_latency_stability(5.0) > normalize_latency_stability(20.0)
