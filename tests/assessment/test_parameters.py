"""Tests for learning parameter derivation.

Tests verify:
- Determinism: same profile → same parameters
- Range constraints: all floats [0,1], specific integers [0-5]
- Floor/round operations for integer parameters
- All 32 parameters computed and in range
"""

import pytest

from backend.assessment.parameters import compute_learning_parameters
from backend.assessment.schemas import ProfileVector


class TestParametersDeterminism:
    """Verify deterministic output: same profile → same parameters."""
    
    def test_deterministic_computation(self):
        """Same ProfileVector should produce identical parameters multiple times."""
        profile = ProfileVector(
            cognitive_capacity=0.75,
            attention_stability=0.68,
            learning_tolerance=0.82,
            motor_baseline=0.65,
            stress_resilience=0.71,
            time_constraint=0.55,
        )
        
        params1 = compute_learning_parameters(profile, skill_id="drawing")
        params2 = compute_learning_parameters(profile, skill_id="drawing")
        params3 = compute_learning_parameters(profile, skill_id="drawing")
        
        # Check all fields are identical
        for field in params1.model_fields.keys():
            v1 = getattr(params1, field)
            v2 = getattr(params2, field)
            v3 = getattr(params3, field)
            assert v1 == v2 == v3, f"Mismatch in {field}: {v1} != {v2} != {v3}"


class TestParametersRangeConstraints:
    """Verify all outputs are within valid ranges."""
    
    def test_float_parameters_in_range(self):
        """All float parameters must be in [0, 1]."""
        profile = ProfileVector(
            cognitive_capacity=0.6,
            attention_stability=0.65,
            learning_tolerance=0.7,
            motor_baseline=0.5,
            stress_resilience=0.75,
            time_constraint=0.55,
        )
        params = compute_learning_parameters(profile, skill_id="guitar")
        
        # Float parameters (all except the 4 integer ones)
        float_fields = [
            "difficulty_slope", "phase_pacing", "entry_phase_offset",
            "repetition_intensity", "session_duration", "fatigue_threshold",
            "break_frequency", "technique_density", "abstraction_level",
            "instruction_granularity", "checkpoint_frequency", "checkpoint_rigidity",
            "error_tolerance_threshold", "drill_depth", "variation_intensity",
            "stress_exposure_rate", "simulation_complexity", "feedback_detail_level",
            "correction_delay_window", "hint_activation_threshold", "precision_requirement",
            "speed_requirement", "coordination_complexity", "adaptation_sensitivity",
            "risk_zone_trigger_level", "regression_policy_strength",
            "phase_transition_sensitivity", "complexity_escalation_trigger",
            "plateau_detection_threshold", "stability_requirement_before_advance",
        ]
        
        for field in float_fields:
            value = getattr(params, field)
            assert isinstance(value, float), f"{field} is not float: {type(value)}"
            assert 0.0 <= value <= 1.0, f"{field} out of range: {value}"
    
    def test_integer_parameters_in_range(self):
        """Integer parameters must be in specific ranges."""
        profile = ProfileVector(
            cognitive_capacity=0.6,
            attention_stability=0.65,
            learning_tolerance=0.7,
            motor_baseline=0.5,
            stress_resilience=0.75,
            time_constraint=0.55,
        )
        params = compute_learning_parameters(profile, skill_id="python")
        
        # micro_session_enabled: 0 or 1
        assert params.micro_session_enabled in [0, 1]
        
        # concurrent_technique_limit: 0-5
        assert 0 <= params.concurrent_technique_limit <= 5
        
        # retry_limit: 0-5
        assert 0 <= params.retry_limit <= 5


class TestIntegerParameterOperations:
    """Test floor and round operations for integer parameters."""
    
    def test_concurrent_technique_limit_floor(self):
        """concurrent_technique_limit = floor(technique_density * 5)."""
        # Low technique density → low limit
        profile = ProfileVector(
            cognitive_capacity=0.1,
            attention_stability=0.1,
            learning_tolerance=0.5,
            motor_baseline=0.5,
            stress_resilience=0.5,
            time_constraint=0.5,
        )
        params = compute_learning_parameters(profile, skill_id="test")
        assert params.concurrent_technique_limit <= 1
        
        # High technique density → high limit
        profile_high = ProfileVector(
            cognitive_capacity=0.9,
            attention_stability=0.9,
            learning_tolerance=0.5,
            motor_baseline=0.5,
            stress_resilience=0.5,
            time_constraint=0.5,
        )
        params_high = compute_learning_parameters(profile_high, skill_id="test")
        assert params_high.concurrent_technique_limit >= 4
    
    def test_retry_limit_round(self):
        """retry_limit = round(learning_tolerance * 5)."""
        # Low tolerance → low retries
        profile_low = ProfileVector(
            cognitive_capacity=0.5,
            attention_stability=0.5,
            learning_tolerance=0.1,
            motor_baseline=0.5,
            stress_resilience=0.5,
            time_constraint=0.5,
        )
        params_low = compute_learning_parameters(profile_low, skill_id="test")
        assert params_low.retry_limit <= 1
        
        # High tolerance → high retries
        profile_high = ProfileVector(
            cognitive_capacity=0.5,
            attention_stability=0.5,
            learning_tolerance=0.9,
            motor_baseline=0.5,
            stress_resilience=0.5,
            time_constraint=0.5,
        )
        params_high = compute_learning_parameters(profile_high, skill_id="test")
        assert params_high.retry_limit >= 4
    
    def test_micro_session_enabled_threshold(self):
        """micro_session_enabled = 1 if attention_stability < 0.4 else 0."""
        # Below threshold
        profile_low = ProfileVector(
            cognitive_capacity=0.5,
            attention_stability=0.3,
            learning_tolerance=0.5,
            motor_baseline=0.5,
            stress_resilience=0.5,
            time_constraint=0.5,
        )
        params_low = compute_learning_parameters(profile_low, skill_id="test")
        assert params_low.micro_session_enabled == 1
        
        # Above threshold
        profile_high = ProfileVector(
            cognitive_capacity=0.5,
            attention_stability=0.5,
            learning_tolerance=0.5,
            motor_baseline=0.5,
            stress_resilience=0.5,
            time_constraint=0.5,
        )
        params_high = compute_learning_parameters(profile_high, skill_id="test")
        assert params_high.micro_session_enabled == 0


class TestParameterBoundaryValues:
    """Test parameter behavior at boundary profile values."""
    
    def test_all_zero_profile(self):
        """All-zero profile should produce valid parameters."""
        profile = ProfileVector(
            cognitive_capacity=0.0,
            attention_stability=0.0,
            learning_tolerance=0.0,
            motor_baseline=0.0,
            stress_resilience=0.0,
            time_constraint=0.0,
        )
        params = compute_learning_parameters(profile, skill_id="test")
        
        # Verify all parameters exist and are in range
        assert params.difficulty_slope == 0.0
        assert params.repetition_intensity == 1.0  # 1 - 0 = 1
        assert params.concurrent_technique_limit == 0
    
    def test_all_one_profile(self):
        """All-one profile should produce valid parameters."""
        profile = ProfileVector(
            cognitive_capacity=1.0,
            attention_stability=1.0,
            learning_tolerance=1.0,
            motor_baseline=1.0,
            stress_resilience=1.0,
            time_constraint=1.0,
        )
        params = compute_learning_parameters(profile, skill_id="test")
        
        # Verify all parameters exist and are in range
        assert params.difficulty_slope == 1.0
        assert params.repetition_intensity == 0.0  # 1 - 1 = 0
        assert params.concurrent_technique_limit == 5


class TestParameterConsistency:
    """Test consistency between related parameters."""
    
    def test_high_cognitive_capacity_effects(self):
        """High cognitive_capacity should increase instruction detail and complexity."""
        profile_high = ProfileVector(
            cognitive_capacity=0.9,
            attention_stability=0.5,
            learning_tolerance=0.5,
            motor_baseline=0.5,
            stress_resilience=0.5,
            time_constraint=0.5,
        )
        profile_low = ProfileVector(
            cognitive_capacity=0.2,
            attention_stability=0.5,
            learning_tolerance=0.5,
            motor_baseline=0.5,
            stress_resilience=0.5,
            time_constraint=0.5,
        )
        
        params_high = compute_learning_parameters(profile_high, skill_id="test")
        params_low = compute_learning_parameters(profile_low, skill_id="test")
        
        # Higher capacity → higher abstraction
        assert params_high.abstraction_level > params_low.abstraction_level
        # Higher capacity → lower instruction granularity (less detail)
        assert params_high.instruction_granularity < params_low.instruction_granularity
    
    def test_high_attention_stability_effects(self):
        """High attention_stability should reduce break frequency."""
        profile_high = ProfileVector(
            cognitive_capacity=0.5,
            attention_stability=0.9,
            learning_tolerance=0.5,
            motor_baseline=0.5,
            stress_resilience=0.5,
            time_constraint=0.5,
        )
        profile_low = ProfileVector(
            cognitive_capacity=0.5,
            attention_stability=0.2,
            learning_tolerance=0.5,
            motor_baseline=0.5,
            stress_resilience=0.5,
            time_constraint=0.5,
        )
        
        params_high = compute_learning_parameters(profile_high, skill_id="test")
        params_low = compute_learning_parameters(profile_low, skill_id="test")
        
        # Higher stability → lower break frequency
        assert params_high.break_frequency < params_low.break_frequency
    
    def test_low_learning_tolerance_effects(self):
        """Low learning_tolerance should use strict error tolerance."""
        profile_low_tol = ProfileVector(
            cognitive_capacity=0.5,
            attention_stability=0.5,
            learning_tolerance=0.2,
            motor_baseline=0.5,
            stress_resilience=0.5,
            time_constraint=0.5,
        )
        profile_high_tol = ProfileVector(
            cognitive_capacity=0.5,
            attention_stability=0.5,
            learning_tolerance=0.9,
            motor_baseline=0.5,
            stress_resilience=0.5,
            time_constraint=0.5,
        )
        
        params_low = compute_learning_parameters(profile_low_tol, skill_id="test")
        params_high = compute_learning_parameters(profile_high_tol, skill_id="test")
        
        # error_tolerance_threshold = learning_tolerance, so low tolerance = low threshold
        assert params_low.error_tolerance_threshold < params_high.error_tolerance_threshold


class TestParametersCompleteness:
    """Verify all 33 parameters are computed."""
    
    def test_all_33_parameters_exist(self):
        """All 33 parameters must be present in output (32 learning params + 1 metadata)."""
        profile = ProfileVector(
            cognitive_capacity=0.5,
            attention_stability=0.5,
            learning_tolerance=0.5,
            motor_baseline=0.5,
            stress_resilience=0.5,
            time_constraint=0.5,
        )
        params = compute_learning_parameters(profile, skill_id="test")
        
        expected_fields = {
            # Group A (4)
            "difficulty_slope", "phase_pacing", "entry_phase_offset",
            "repetition_intensity",
            # Group B (4)
            "session_duration", "micro_session_enabled", "fatigue_threshold",
            "break_frequency",
            # Group C (4)
            "technique_density", "concurrent_technique_limit", "abstraction_level",
            "instruction_granularity",
            # Group D (4)
            "checkpoint_frequency", "checkpoint_rigidity", "error_tolerance_threshold",
            "retry_limit",
            # Group E (4)
            "drill_depth", "variation_intensity", "stress_exposure_rate",
            "simulation_complexity",
            # Group F (3)
            "feedback_detail_level", "correction_delay_window", "hint_activation_threshold",
            # Group G (3)
            "precision_requirement", "speed_requirement", "coordination_complexity",
            # Group H (7)
            "adaptation_sensitivity", "risk_zone_trigger_level", "regression_policy_strength",
            "phase_transition_sensitivity", "complexity_escalation_trigger",
            "plateau_detection_threshold", "stability_requirement_before_advance",
        }
        
        actual_fields = set(params.model_fields.keys())
        # 32 learning parameters (A-H) expected
        assert len(actual_fields) == len(expected_fields), f"Expected {len(expected_fields)} parameters, got {len(actual_fields)}"
        assert expected_fields == actual_fields, f"Missing or extra fields"


class TestSkillIdParameter:
    """Verify skill_id parameter (prepared for future skill-specific overrides)."""
    
    def test_skill_id_accepted(self):
        """skill_id parameter should be accepted without error."""
        profile = ProfileVector(
            cognitive_capacity=0.5,
            attention_stability=0.5,
            learning_tolerance=0.5,
            motor_baseline=0.5,
            stress_resilience=0.5,
            time_constraint=0.5,
        )
        
        # Test with various skill IDs
        for skill_id in ["drawing", "guitar", "python-basics", "language-spanish"]:
            params = compute_learning_parameters(profile, skill_id=skill_id)
            assert params is not None
