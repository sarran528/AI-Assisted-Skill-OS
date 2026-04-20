"""Tests for skill-specific learning parameter mapping."""

import pytest

from backend.assessment.parameters import compute_learning_parameters
from backend.assessment.profile_vector import compute_profile_vector
from backend.assessment.schemas import (
    LearningParameters,
    NormalizedSignals,
    ProfileVector,
)
from backend.assessment.skill_mapping import (
    DOMAINS,
    _apply_art_overrides,
    _apply_language_overrides,
    _apply_music_overrides,
    _apply_physical_overrides,
    _apply_programming_overrides,
    apply_skill_mapping,
)
from backend.shared.llm.schemas import (
    DEFAULT_SKILL_MODIFIERS,
    SkillModifierResult,
)


@pytest.fixture
def base_profile() -> ProfileVector:
    """Create a base ProfileVector for testing."""
    return ProfileVector(
        cognitive_capacity=0.6,
        attention_stability=0.7,
        learning_tolerance=0.5,
        motor_baseline=0.6,
        stress_resilience=0.7,
        time_constraint=0.8,
    )


@pytest.fixture
def base_parameters(base_profile: ProfileVector) -> LearningParameters:
    """Create base LearningParameters from ProfileVector."""
    return compute_learning_parameters(base_profile, skill_id="baseline")


class TestArtOverrides:
    """Test art domain-specific overrides."""

    def test_difficulty_slope_increased(self, base_parameters):
        """Test that difficulty_slope is increased."""
        original_slope = base_parameters.difficulty_slope
        result = _apply_art_overrides(base_parameters)
        assert result.difficulty_slope > original_slope
        assert result.difficulty_slope <= 1.0

    def test_drill_depth_increased(self, base_parameters):
        """Test that drill_depth is increased for repetitive practice."""
        original_depth = base_parameters.drill_depth
        result = _apply_art_overrides(base_parameters)
        assert result.drill_depth > original_depth
        assert result.drill_depth <= 1.0

    def test_checkpoint_rigidity_tightened(self, base_parameters):
        """Test that checkpoint_rigidity is tightened."""
        original_rigidity = base_parameters.checkpoint_rigidity
        result = _apply_art_overrides(base_parameters)
        assert result.checkpoint_rigidity >= original_rigidity
        assert result.checkpoint_rigidity <= 1.0

    def test_immutable_input(self, base_parameters):
        """Test that input is never mutated."""
        original_slope = base_parameters.difficulty_slope
        original_depth = base_parameters.drill_depth
        _apply_art_overrides(base_parameters)
        assert base_parameters.difficulty_slope == original_slope
        assert base_parameters.drill_depth == original_depth


class TestMusicOverrides:
    """Test music domain-specific overrides."""

    def test_repetition_intensity_increased(self, base_parameters):
        """Test that repetition_intensity is increased."""
        original_intensity = base_parameters.repetition_intensity
        result = _apply_music_overrides(base_parameters)
        assert result.repetition_intensity >= original_intensity
        assert result.repetition_intensity <= 1.0

    def test_repetition_intensity_floor_enforced(self):
        """Test that repetition_intensity has a floor of 0.6."""
        # Create parameters with low repetition_intensity
        params = LearningParameters(
            difficulty_slope=0.5,
            phase_pacing=0.5,
            entry_phase_offset=0.5,
            repetition_intensity=0.2,  # Very low
            session_duration=0.5,
            micro_session_enabled=0,
            fatigue_threshold=0.5,
            break_frequency=0.5,
            technique_density=0.5,
            concurrent_technique_limit=2,
            abstraction_level=0.5,
            instruction_granularity=0.5,
            checkpoint_frequency=0.5,
            checkpoint_rigidity=0.5,
            error_tolerance_threshold=0.5,
            retry_limit=2,
            drill_depth=0.5,
            variation_intensity=0.5,
            stress_exposure_rate=0.5,
            simulation_complexity=0.5,
            feedback_detail_level=0.5,
            correction_delay_window=0.5,
            hint_activation_threshold=0.5,
            precision_requirement=0.5,
            speed_requirement=0.5,
            coordination_complexity=0.5,
            adaptation_sensitivity=0.5,
            risk_zone_trigger_level=0.5,
            regression_policy_strength=0.5,
            phase_transition_sensitivity=0.5,
            complexity_escalation_trigger=0.5,
            plateau_detection_threshold=0.5,
            stability_requirement_before_advance=0.5,
        )

        result = _apply_music_overrides(params)
        assert result.repetition_intensity >= 0.6

    def test_checkpoint_rigidity_tightened(self, base_parameters):
        """Test that checkpoint_rigidity is tightened."""
        original_rigidity = base_parameters.checkpoint_rigidity
        result = _apply_music_overrides(base_parameters)
        assert result.checkpoint_rigidity >= original_rigidity
        assert result.checkpoint_rigidity <= 1.0


class TestProgrammingOverrides:
    """Test programming domain-specific overrides."""

    def test_abstraction_level_increased(self, base_parameters):
        """Test that abstraction_level is increased."""
        original_level = base_parameters.abstraction_level
        result = _apply_programming_overrides(base_parameters)
        assert result.abstraction_level > original_level
        assert result.abstraction_level <= 1.0

    def test_technique_density_capped_for_low_capacity(self):
        """Test that technique_density is capped for lower-capacity learners."""
        # Create parameters with low difficulty_slope
        params = LearningParameters(
            difficulty_slope=0.4,  # Low capacity
            phase_pacing=0.5,
            entry_phase_offset=0.5,
            repetition_intensity=0.5,
            session_duration=0.5,
            micro_session_enabled=0,
            fatigue_threshold=0.5,
            break_frequency=0.5,
            technique_density=0.8,  # High density
            concurrent_technique_limit=4,
            abstraction_level=0.5,
            instruction_granularity=0.5,
            checkpoint_frequency=0.5,
            checkpoint_rigidity=0.5,
            error_tolerance_threshold=0.5,
            retry_limit=2,
            drill_depth=0.5,
            variation_intensity=0.5,
            stress_exposure_rate=0.5,
            simulation_complexity=0.5,
            feedback_detail_level=0.5,
            correction_delay_window=0.5,
            hint_activation_threshold=0.5,
            precision_requirement=0.5,
            speed_requirement=0.5,
            coordination_complexity=0.5,
            adaptation_sensitivity=0.5,
            risk_zone_trigger_level=0.5,
            regression_policy_strength=0.5,
            phase_transition_sensitivity=0.5,
            complexity_escalation_trigger=0.5,
            plateau_detection_threshold=0.5,
            stability_requirement_before_advance=0.5,
        )

        result = _apply_programming_overrides(params)
        assert result.technique_density <= 0.5


class TestLanguageOverrides:
    """Test language domain-specific overrides."""

    def test_phase_pacing_adjusted(self, base_parameters):
        """Test that phase_pacing is adjusted."""
        original_pacing = base_parameters.phase_pacing
        result = _apply_language_overrides(base_parameters)
        assert result.phase_pacing > original_pacing
        assert result.phase_pacing <= 1.0

    def test_variation_intensity_increased(self, base_parameters):
        """Test that variation_intensity is increased."""
        original_variation = base_parameters.variation_intensity
        result = _apply_language_overrides(base_parameters)
        assert result.variation_intensity > original_variation
        assert result.variation_intensity <= 1.0


class TestPhysicalOverrides:
    """Test physical domain-specific overrides."""

    def test_motor_parameters_emphasized(self, base_parameters):
        """Test that motor parameters are emphasized."""
        original_precision = base_parameters.precision_requirement
        original_coordination = base_parameters.coordination_complexity
        result = _apply_physical_overrides(base_parameters)
        assert result.precision_requirement >= original_precision
        assert result.coordination_complexity >= original_coordination

    def test_drill_depth_increased(self, base_parameters):
        """Test that drill_depth is increased for repetition."""
        original_depth = base_parameters.drill_depth
        result = _apply_physical_overrides(base_parameters)
        assert result.drill_depth > original_depth
        assert result.drill_depth <= 1.0


class TestGlobalRules:
    """Test global override rules."""

    def test_technique_density_cap_enforced(self):
        """Test global rule: cap technique_density if both high."""
        params = LearningParameters(
            difficulty_slope=0.5,
            phase_pacing=0.5,
            entry_phase_offset=0.5,
            repetition_intensity=0.5,
            session_duration=0.5,
            micro_session_enabled=0,
            fatigue_threshold=0.5,
            break_frequency=0.5,
            technique_density=0.9,  # High
            concurrent_technique_limit=4,
            abstraction_level=0.5,
            instruction_granularity=0.5,
            checkpoint_frequency=0.5,
            checkpoint_rigidity=0.5,
            error_tolerance_threshold=0.5,
            retry_limit=2,
            drill_depth=0.5,
            variation_intensity=0.5,
            stress_exposure_rate=0.5,
            simulation_complexity=0.5,
            feedback_detail_level=0.5,
            correction_delay_window=0.5,
            hint_activation_threshold=0.5,
            precision_requirement=0.5,
            speed_requirement=0.5,
            coordination_complexity=0.5,
            adaptation_sensitivity=0.5,
            risk_zone_trigger_level=0.5,
            regression_policy_strength=0.5,
            phase_transition_sensitivity=0.5,
            complexity_escalation_trigger=0.5,
            plateau_detection_threshold=0.5,
            stability_requirement_before_advance=0.5,
        )

        # Apply skill mapping with high complexity
        result = apply_skill_mapping(
            params,
            domain="programming",
            complexity_score=0.8,  # High complexity
            skill_modifiers=DEFAULT_SKILL_MODIFIERS,
            skill_id="test",
        )

        assert result.technique_density <= 0.7


class TestModifierIntegration:
    """Test LLM modifier integration."""

    def test_modifiers_applied_and_clamped(self, base_parameters):
        """Test that modifiers are applied and clamped correctly."""
        # Create custom modifiers
        modifiers = SkillModifierResult(
            technique_density_adjustment=0.2,
            repetition_boost=0.15,
            notes="test",
        )

        result = apply_skill_mapping(
            base_parameters,
            domain="other",
            complexity_score=0.5,
            skill_modifiers=modifiers,
            skill_id="test",
        )

        # Verify modifiers were applied (approximately)
        assert result.technique_density > base_parameters.technique_density
        assert result.repetition_intensity > base_parameters.repetition_intensity


class TestSkillMappingMainFunction:
    """Test main apply_skill_mapping function."""

    def test_full_flow_marks_adjusted(self, base_parameters):
        """Test that full flow marks parameters as skill-adjusted."""
        result = apply_skill_mapping(
            base_parameters,
            domain="art",
            complexity_score=0.5,
            skill_modifiers=DEFAULT_SKILL_MODIFIERS,
            skill_id="drawing",
        )

        assert result.is_skill_adjusted is True
        assert result.skill_id == "drawing"

    def test_unknown_domain_handled(self, base_parameters):
        """Test that unknown domains don't cause errors."""
        result = apply_skill_mapping(
            base_parameters,
            domain="unknown",
            complexity_score=0.5,
            skill_modifiers=DEFAULT_SKILL_MODIFIERS,
            skill_id="test",
        )

        assert result.is_skill_adjusted is True
        assert result.skill_id == "test"

    def test_immutability_of_input(self, base_parameters):
        """Test that input parameters are never mutated."""
        original_dump = base_parameters.model_dump()

        apply_skill_mapping(
            base_parameters,
            domain="programming",
            complexity_score=0.7,
            skill_modifiers=DEFAULT_SKILL_MODIFIERS,
            skill_id="python",
        )

        # Verify input unchanged
        assert base_parameters.model_dump() == original_dump
