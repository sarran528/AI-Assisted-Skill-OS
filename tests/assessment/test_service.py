"""Integration tests for assessment service.

Tests the end-to-end flow from raw submission to profile vector.
"""

import pytest
from uuid import uuid4

from backend.assessment.schemas import (
    AssessmentSubmission,
    RawMetrics,
    RawTimeConstraint,
)
from backend.assessment.service import process_assessment, serialize_profile_vector, serialize_normalized_signals


class TestAssessmentServiceEndToEnd:
    """Test complete assessment processing flow."""
    
    @pytest.mark.asyncio
    async def test_process_assessment_complete(self):
        """Test complete assessment processing without DB (mock session)."""
        submission = AssessmentSubmission(
            level=1,
            metrics=RawMetrics(
                accuracy=84.0,
                expected_time=2.9,
                latency_stability=8.4,
                decay_inverse=0.78,
                dropout=1,
                retry=2,
                recovery=0.73,
            ),
            time_constraint=RawTimeConstraint(
                available_hours_per_week=20.0,
                preferred_session_length=75.0,
            ),
        )
        
        # Process without DB (mock)
        user_id = uuid4()
        profile = await process_assessment(None, user_id, submission)
        
        # Verify profile computed
        assert profile is not None
        assert profile.profile_vector is not None
        assert profile.raw_signals is not None
        
        # Verify all 6 dimensions are in range
        assert 0.0 <= profile.profile_vector.cognitive_capacity <= 1.0
        assert 0.0 <= profile.profile_vector.attention_stability <= 1.0
        assert 0.0 <= profile.profile_vector.learning_tolerance <= 1.0
        assert 0.0 <= profile.profile_vector.motor_baseline <= 1.0
        assert 0.0 <= profile.profile_vector.stress_resilience <= 1.0
        assert 0.0 <= profile.profile_vector.time_constraint <= 1.0


class TestSerialization:
    """Test serialization helpers."""
    
    def test_serialize_profile_vector(self):
        """Verify profile vector serialization."""
        from backend.assessment.schemas import ProfileVector
        
        vector = ProfileVector(
            cognitive_capacity=0.75,
            attention_stability=0.68,
            learning_tolerance=0.82,
            motor_baseline=0.65,
            stress_resilience=0.71,
            time_constraint=0.55,
        )
        
        serialized = serialize_profile_vector(vector)
        
        assert isinstance(serialized, dict)
        assert len(serialized) == 6
        assert serialized["cognitive_capacity"] == 0.75
        assert serialized["attention_stability"] == 0.68
        assert serialized["learning_tolerance"] == 0.82
    
    def test_serialize_normalized_signals(self):
        """Verify normalized signals serialization."""
        from backend.assessment.schemas import NormalizedSignals
        
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
        
        serialized = serialize_normalized_signals(signals)
        
        assert isinstance(serialized, dict)
        assert len(serialized) == 9
        assert serialized["n_accuracy"] == 0.84
        assert serialized["n_latency"] == 0.71
