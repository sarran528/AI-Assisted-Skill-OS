"""
Parameter derivation service - generates 32 learning parameters from profile.
"""
from decimal import Decimal
from uuid import uuid4
from datetime import datetime
from backend.shared.models import LearningParametersModel


class ParameterService:
    """Derives learning parameters from cognitive profile."""

    @staticmethod
    def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Clamp a value between min and max."""
        return max(min_val, min(max_val, value))

    @staticmethod
    def derive_parameters(
        profile: dict,
        skill_id: str,
        profile_id: str,
    ) -> dict:
        """
        Derive all 32 learning parameters from profile vector.
        
        Args:
            profile: Dict with keys: cognitive_capacity, attention_stability, learning_tolerance,
                    motor_baseline, stress_resilience, time_constraint
            skill_id: Target skill ID
            profile_id: Link to cognitive_profiles table
            
        Returns:
            Dict with all 32 parameters for insertion
        """
        cc = float(profile.get("cognitive_capacity", 0.5))
        atn = float(profile.get("attention_stability", 0.5))
        lt = float(profile.get("learning_tolerance", 0.5))
        mb = float(profile.get("motor_baseline", 0.5))
        sr = float(profile.get("stress_resilience", 0.5))
        tc = float(profile.get("time_constraint", 0.5))

        # Group A — Progression Control
        difficulty_slope = ParameterService.clamp(cc * 0.8 + lt * 0.2)
        phase_pacing = ParameterService.clamp(tc * 0.6 + atn * 0.4)
        entry_phase_offset = ParameterService.clamp(cc * 0.5 + lt * 0.5)
        repetition_intensity = ParameterService.clamp(1.0 - sr * 0.5)

        # Group B — Session Structure
        session_duration = ParameterService.clamp(tc * 0.7 + atn * 0.3)
        micro_session_enabled = 1 if tc < 0.4 else 0
        fatigue_threshold = ParameterService.clamp(atn * 0.6 + sr * 0.4)
        break_frequency = ParameterService.clamp(1.0 - (atn * 0.7 + sr * 0.3))

        # Group C — Cognitive Load
        technique_density = ParameterService.clamp(cc * 0.8)
        concurrent_technique_limit = min(5, max(1, int(cc * 5)))
        abstraction_level = ParameterService.clamp(cc * 0.9)
        instruction_granularity = ParameterService.clamp(1.0 - atn * 0.4)

        # Group D — Validation
        checkpoint_frequency = ParameterService.clamp(1.0 - lt * 0.5)
        checkpoint_rigidity = ParameterService.clamp(sr * 0.6 + atn * 0.4)
        error_tolerance_threshold = ParameterService.clamp(lt * 0.7)
        retry_limit = min(5, max(1, int((1.0 - sr) * 5)))

        # Group E — Practice Dynamics
        drill_depth = ParameterService.clamp(cc * 0.7 + mb * 0.3)
        variation_intensity = ParameterService.clamp(sr * 0.5 + lt * 0.5)
        stress_exposure_rate = ParameterService.clamp(1.0 - sr * 0.6)
        simulation_complexity = ParameterService.clamp(cc * 0.8 + mb * 0.2)

        # Group F — Feedback
        feedback_detail_level = ParameterService.clamp(atn * 0.7 + cc * 0.3)
        correction_delay_window = ParameterService.clamp(1.0 - atn * 0.5)
        hint_activation_threshold = ParameterService.clamp(lt * 0.6)

        # Group G — Motor
        precision_requirement = ParameterService.clamp(mb * 0.9)
        speed_requirement = ParameterService.clamp(atn * 0.8)
        coordination_complexity = ParameterService.clamp(mb * 0.7 + cc * 0.3)

        # Group H — Adaptive Meta
        adaptation_sensitivity = ParameterService.clamp(atn * 0.8)
        risk_zone_trigger_level = ParameterService.clamp(1.0 - ((lt + sr) / 2.0) * 0.8)
        regression_policy_strength = ParameterService.clamp(sr * 0.5)
        phase_transition_sensitivity = ParameterService.clamp(cc * 0.6 + lt * 0.4)
        complexity_escalation_trigger = ParameterService.clamp(cc * 0.7 + atn * 0.3)
        plateau_detection_threshold = ParameterService.clamp(atn * 0.5 + sr * 0.5)
        stability_requirement_before_advance = ParameterService.clamp(sr * 0.6 + lt * 0.4)

        return {
            "id": str(uuid4()),
            "profile_id": profile_id,
            "skill_id": skill_id,
            "difficulty_slope": Decimal(str(round(difficulty_slope, 4))),
            "phase_pacing": Decimal(str(round(phase_pacing, 4))),
            "entry_phase_offset": Decimal(str(round(entry_phase_offset, 4))),
            "repetition_intensity": Decimal(str(round(repetition_intensity, 4))),
            "session_duration": Decimal(str(round(session_duration, 4))),
            "micro_session_enabled": micro_session_enabled,
            "fatigue_threshold": Decimal(str(round(fatigue_threshold, 4))),
            "break_frequency": Decimal(str(round(break_frequency, 4))),
            "technique_density": Decimal(str(round(technique_density, 4))),
            "concurrent_technique_limit": concurrent_technique_limit,
            "abstraction_level": Decimal(str(round(abstraction_level, 4))),
            "instruction_granularity": Decimal(str(round(instruction_granularity, 4))),
            "checkpoint_frequency": Decimal(str(round(checkpoint_frequency, 4))),
            "checkpoint_rigidity": Decimal(str(round(checkpoint_rigidity, 4))),
            "error_tolerance_threshold": Decimal(str(round(error_tolerance_threshold, 4))),
            "retry_limit": retry_limit,
            "drill_depth": Decimal(str(round(drill_depth, 4))),
            "variation_intensity": Decimal(str(round(variation_intensity, 4))),
            "stress_exposure_rate": Decimal(str(round(stress_exposure_rate, 4))),
            "simulation_complexity": Decimal(str(round(simulation_complexity, 4))),
            "feedback_detail_level": Decimal(str(round(feedback_detail_level, 4))),
            "correction_delay_window": Decimal(str(round(correction_delay_window, 4))),
            "hint_activation_threshold": Decimal(str(round(hint_activation_threshold, 4))),
            "precision_requirement": Decimal(str(round(precision_requirement, 4))),
            "speed_requirement": Decimal(str(round(speed_requirement, 4))),
            "coordination_complexity": Decimal(str(round(coordination_complexity, 4))),
            "adaptation_sensitivity": Decimal(str(round(adaptation_sensitivity, 4))),
            "risk_zone_trigger_level": Decimal(str(round(risk_zone_trigger_level, 4))),
            "regression_policy_strength": Decimal(str(round(regression_policy_strength, 4))),
            "phase_transition_sensitivity": Decimal(str(round(phase_transition_sensitivity, 4))),
            "complexity_escalation_trigger": Decimal(str(round(complexity_escalation_trigger, 4))),
            "plateau_detection_threshold": Decimal(str(round(plateau_detection_threshold, 4))),
            "stability_requirement_before_advance": Decimal(str(round(stability_requirement_before_advance, 4))),
            "created_at": datetime.utcnow(),
        }
