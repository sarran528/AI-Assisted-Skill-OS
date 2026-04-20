"""Tests for profile vector computation.

Tests verify:
- Weight sums equal 1.0 for each dimension
- Deterministic output (same input = same output)
- Range constraints (all 0-1)
- Known input → known output verification
"""

import pytest

from backend.assessment.normalization import normalize_all
from backend.assessment.profile_vector import compute_profile_vector
from backend.assessment.schemas import (
    NormalizedSignals,
    ProfileVector,
    RawMetrics,
    RawTimeConstraint,
)


class TestProfileVectorWeights:
    """Verify that each dimension's weights sum to 1.0.
    
    When all signals are set to 1.0, each dimension should equal 1.0
    because weight_a + weight_b + weight_c + ... = 1.0.
    """
    
    def test_cognitive_capacity_weights(self):
        """cognitive_capacity weights: 0.35 + 0.20 + 0.15 + 0.10 + 0.20 = 1.0."""
        signals = NormalizedSignals(
            n_accuracy=1.0,
            n_latency=1.0,
            n_latency_stability=1.0,
            n_decay_inverse=1.0,
            n_dropout=1.0,
            n_retry=1.0,
            n_recovery=1.0,
            n_hours=1.0,
            n_session_pref=1.0,
        )
        profile = compute_profile_vector(signals)
        assert abs(profile.cognitive_capacity - 1.0) < 1e-9
    
    def test_attention_stability_weights(self):
        """attention_stability weights: 0.50 + 0.50 = 1.0."""
        signals = NormalizedSignals(
            n_accuracy=0.0,
            n_latency=0.0,
            n_latency_stability=1.0,
            n_decay_inverse=1.0,
            n_dropout=0.0,
            n_retry=0.0,
            n_recovery=0.0,
            n_hours=0.0,
            n_session_pref=0.0,
        )
        profile = compute_profile_vector(signals)
        assert abs(profile.attention_stability - 1.0) < 1e-9
    
    def test_learning_tolerance_weights(self):
        """learning_tolerance weights: 0.40 + 0.40 + 0.20 = 1.0."""
        signals = NormalizedSignals(
            n_accuracy=0.0,
            n_latency=0.0,
            n_latency_stability=0.0,
            n_decay_inverse=0.0,
            n_dropout=1.0,
            n_retry=1.0,
            n_recovery=1.0,
            n_hours=0.0,
            n_session_pref=0.0,
        )
        profile = compute_profile_vector(signals)
        assert abs(profile.learning_tolerance - 1.0) < 1e-9
    
    def test_motor_baseline_weights(self):
        """motor_baseline weights: 0.60 + 0.40 = 1.0."""
        signals = NormalizedSignals(
            n_accuracy=0.0,
            n_latency=1.0,
            n_latency_stability=1.0,
            n_decay_inverse=0.0,
            n_dropout=0.0,
            n_retry=0.0,
            n_recovery=0.0,
            n_hours=0.0,
            n_session_pref=0.0,
        )
        profile = compute_profile_vector(signals)
        assert abs(profile.motor_baseline - 1.0) < 1e-9
    
    def test_stress_resilience_weights(self):
        """stress_resilience weights: 0.60 + 0.40 = 1.0."""
        signals = NormalizedSignals(
            n_accuracy=0.0,
            n_latency=0.0,
            n_latency_stability=0.0,
            n_decay_inverse=1.0,
            n_dropout=0.0,
            n_retry=0.0,
            n_recovery=1.0,
            n_hours=0.0,
            n_session_pref=0.0,
        )
        profile = compute_profile_vector(signals)
        assert abs(profile.stress_resilience - 1.0) < 1e-9
    
    def test_time_constraint_weights(self):
        """time_constraint weights: 0.70 + 0.30 = 1.0."""
        signals = NormalizedSignals(
            n_accuracy=0.0,
            n_latency=0.0,
            n_latency_stability=0.0,
            n_decay_inverse=0.0,
            n_dropout=0.0,
            n_retry=0.0,
            n_recovery=0.0,
            n_hours=1.0,
            n_session_pref=1.0,
        )
        profile = compute_profile_vector(signals)
        assert abs(profile.time_constraint - 1.0) < 1e-9


class TestProfileVectorBoundaries:
    """Test boundary behavior: all zeros should produce all zeros."""
    
    def test_all_zero_signals(self):
        """All signals at 0 should produce all dimensions at 0."""
        signals = NormalizedSignals(
            n_accuracy=0.0,
            n_latency=0.0,
            n_latency_stability=0.0,
            n_decay_inverse=0.0,
            n_dropout=0.0,
            n_retry=0.0,
            n_recovery=0.0,
            n_hours=0.0,
            n_session_pref=0.0,
        )
        profile = compute_profile_vector(signals)
        assert abs(profile.cognitive_capacity - 0.0) < 1e-9
        assert abs(profile.attention_stability - 0.0) < 1e-9
        assert abs(profile.learning_tolerance - 0.0) < 1e-9
        assert abs(profile.motor_baseline - 0.0) < 1e-9
        assert abs(profile.stress_resilience - 0.0) < 1e-9
        assert abs(profile.time_constraint - 0.0) < 1e-9
    
    def test_all_one_signals(self):
        """All signals at 1 should produce all dimensions at 1."""
        signals = NormalizedSignals(
            n_accuracy=1.0,
            n_latency=1.0,
            n_latency_stability=1.0,
            n_decay_inverse=1.0,
            n_dropout=1.0,
            n_retry=1.0,
            n_recovery=1.0,
            n_hours=1.0,
            n_session_pref=1.0,
        )
        profile = compute_profile_vector(signals)
        assert abs(profile.cognitive_capacity - 1.0) < 1e-9
        assert abs(profile.attention_stability - 1.0) < 1e-9
        assert abs(profile.learning_tolerance - 1.0) < 1e-9
        assert abs(profile.motor_baseline - 1.0) < 1e-9
        assert abs(profile.stress_resilience - 1.0) < 1e-9
        assert abs(profile.time_constraint - 1.0) < 1e-9


class TestProfileVectorRangeConstraints:
    """Verify that all outputs are in [0, 1] regardless of input."""
    
    def test_all_dimensions_in_range(self):
        """All 6 dimensions must be in [0, 1]."""
        signals = NormalizedSignals(
            n_accuracy=0.5,
            n_latency=0.6,
            n_latency_stability=0.7,
            n_decay_inverse=0.8,
            n_dropout=0.4,
            n_retry=0.5,
            n_recovery=0.9,
            n_hours=0.3,
            n_session_pref=0.2,
        )
        profile = compute_profile_vector(signals)
        
        assert 0.0 <= profile.cognitive_capacity <= 1.0
        assert 0.0 <= profile.attention_stability <= 1.0
        assert 0.0 <= profile.learning_tolerance <= 1.0
        assert 0.0 <= profile.motor_baseline <= 1.0
        assert 0.0 <= profile.stress_resilience <= 1.0
        assert 0.0 <= profile.time_constraint <= 1.0


class TestProfileVectorDeterminism:
    """Verify that output is deterministic: same input always produces same output."""
    
    def test_deterministic_output(self):
        """Same input should produce identical output when called multiple times."""
        signals = NormalizedSignals(
            n_accuracy=0.84,
            n_latency=0.71,
            n_latency_stability=0.66,
            n_decay_inverse=0.78,
            n_dropout=0.90,
            n_retry=0.85,
            n_recovery=0.73,
            n_hours=0.50,
            n_session_pref=0.625,
        )
        
        profile1 = compute_profile_vector(signals)
        profile2 = compute_profile_vector(signals)
        profile3 = compute_profile_vector(signals)
        
        assert profile1.cognitive_capacity == profile2.cognitive_capacity == profile3.cognitive_capacity
        assert profile1.attention_stability == profile2.attention_stability == profile3.attention_stability
        assert profile1.learning_tolerance == profile2.learning_tolerance == profile3.learning_tolerance
        assert profile1.motor_baseline == profile2.motor_baseline == profile3.motor_baseline
        assert profile1.stress_resilience == profile2.stress_resilience == profile3.stress_resilience
        assert profile1.time_constraint == profile2.time_constraint == profile3.time_constraint


class TestProfileVectorExpectedValues:
    """Test known input → known output verification."""
    
    def test_balanced_profile(self):
        """All signals at 0.5 should produce reasonable balanced output."""
        signals = NormalizedSignals(
            n_accuracy=0.5,
            n_latency=0.5,
            n_latency_stability=0.5,
            n_decay_inverse=0.5,
            n_dropout=0.5,
            n_retry=0.5,
            n_recovery=0.5,
            n_hours=0.5,
            n_session_pref=0.5,
        )
        profile = compute_profile_vector(signals)
        
        # All dimensions should be close to 0.5 with balanced input
        assert 0.45 < profile.cognitive_capacity < 0.55
        assert 0.45 < profile.attention_stability < 0.55
        assert 0.45 < profile.learning_tolerance < 0.55
        assert 0.45 < profile.motor_baseline < 0.55
        assert 0.45 < profile.stress_resilience < 0.55
        assert 0.45 < profile.time_constraint < 0.55
    
    def test_high_ability_profile(self):
        """High accuracy and low latency should indicate high cognitive capacity."""
        signals = NormalizedSignals(
            n_accuracy=1.0,  # Perfect accuracy
            n_latency=0.9,   # Very fast
            n_latency_stability=0.95,  # Very consistent
            n_decay_inverse=0.8,
            n_dropout=0.7,
            n_retry=0.8,
            n_recovery=0.85,
            n_hours=0.8,
            n_session_pref=0.7,
        )
        profile = compute_profile_vector(signals)
        assert profile.cognitive_capacity > 0.85
    
    def test_low_ability_profile(self):
        """Low accuracy and high latency should indicate low cognitive capacity."""
        signals = NormalizedSignals(
            n_accuracy=0.2,  # Low accuracy
            n_latency=0.1,   # Very slow
            n_latency_stability=0.05,  # Very inconsistent
            n_decay_inverse=0.2,
            n_dropout=0.2,
            n_retry=0.3,
            n_recovery=0.2,
            n_hours=0.2,
            n_session_pref=0.3,
        )
        profile = compute_profile_vector(signals)
        assert profile.cognitive_capacity < 0.3


class TestProfileVectorEndToEnd:
    """End-to-end tests from raw metrics to profile vector."""
    
    def test_end_to_end_flow(self):
        """Test complete flow: raw metrics → normalized → profile."""
        raw_metrics = RawMetrics(
            accuracy=84.0,
            expected_time=2.9,
            latency_stability=8.4,
            decay_inverse=0.78,
            dropout=1,
            retry=2,
            recovery=0.73,
        )
        time_constraint = RawTimeConstraint(
            available_hours_per_week=20.0,
            preferred_session_length=75.0,
        )
        
        # Normalize
        signals = normalize_all(raw_metrics, time_constraint)
        
        # Compute profile
        profile = compute_profile_vector(signals)
        
        # Verify result is valid
        assert isinstance(profile, ProfileVector)
        assert all(0.0 <= getattr(profile, dim) <= 1.0 
                  for dim in profile.model_fields.keys())
