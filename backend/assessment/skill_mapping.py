"""Skill-specific learning parameter adjustments.

Applies domain-specific overrides to raw LearningParameters.
The same cognitive profile produces different learning parameters
for drawing vs programming vs music. This module differentiates.

All functions are pure: they never mutate inputs, always return new instances.
"""

from typing import Callable

from backend.assessment.normalization import _clamp
from backend.assessment.schemas import LearningParameters
from backend.shared.llm.schemas import SkillModifierResult


# Skill domains
DOMAINS = {"art", "music", "programming", "language", "physical", "other"}


def _apply_art_overrides(params: LearningParameters) -> LearningParameters:
    """Apply art domain overrides to learning parameters."""
    data = params.model_dump()

    # Increase difficulty_slope weight toward motor_baseline
    data["difficulty_slope"] = _clamp(data["difficulty_slope"] + 0.15)

    # Increase drill_depth for repetitive physical practice
    data["drill_depth"] = _clamp(data["drill_depth"] + 0.1)

    # Tighten checkpoint_rigidity for precision
    data["checkpoint_rigidity"] = _clamp(data["checkpoint_rigidity"] * 1.1)

    return LearningParameters(**data)


def _apply_music_overrides(params: LearningParameters) -> LearningParameters:
    """Apply music domain overrides to learning parameters."""
    data = params.model_dump()

    # Increase repetition_intensity for motor memory
    data["repetition_intensity"] = _clamp(data["repetition_intensity"] + 0.15)

    # Enforce minimum repetition_intensity of 0.6
    data["repetition_intensity"] = max(data["repetition_intensity"], 0.6)

    # Tighten checkpoint_rigidity for motor checkpoints
    data["checkpoint_rigidity"] = _clamp(data["checkpoint_rigidity"] * 1.2)

    return LearningParameters(**data)


def _apply_programming_overrides(params: LearningParameters) -> LearningParameters:
    """Apply programming domain overrides to learning parameters."""
    data = params.model_dump()

    # Increase abstraction_level (programming is heavily abstract)
    data["abstraction_level"] = _clamp(data["abstraction_level"] + 0.1)

    # Cap technique_density at 0.5 for lower-capacity learners during fundamentals
    # Note: This is applied globally, not phase-specific in this simple version
    if data["difficulty_slope"] < 0.6:
        data["technique_density"] = min(data["technique_density"], 0.5)

    # Increase instruction_granularity for lower-capacity learners
    if params.is_skill_adjusted and data["difficulty_slope"] < 0.6:
        data["instruction_granularity"] = _clamp(data["instruction_granularity"] + 0.1)

    return LearningParameters(**data)


def _apply_language_overrides(params: LearningParameters) -> LearningParameters:
    """Apply language domain overrides to learning parameters."""
    data = params.model_dump()

    # Language phases are typically vocabulary and grammar
    # We increase pacing for vocabulary (earlier phases), decrease for grammar
    # Proxy: use a weighted adjustment based on existing phase_pacing
    data["phase_pacing"] = _clamp(data["phase_pacing"] + 0.05)

    # Increase variation_intensity for varied exposure contexts
    data["variation_intensity"] = _clamp(data["variation_intensity"] + 0.1)

    return LearningParameters(**data)


def _apply_physical_overrides(params: LearningParameters) -> LearningParameters:
    """Apply physical domain overrides to learning parameters."""
    data = params.model_dump()

    # Physical skills rely heavily on motor_baseline
    # Emphasize motor parameters
    data["precision_requirement"] = _clamp(data["precision_requirement"] + 0.1)
    data["coordination_complexity"] = _clamp(data["coordination_complexity"] + 0.1)

    # Increase drill_depth for physical repetition
    data["drill_depth"] = _clamp(data["drill_depth"] + 0.15)

    return LearningParameters(**data)


# Domain override registry
DOMAIN_OVERRIDES: dict[str, Callable[[LearningParameters], LearningParameters]] = {
    "art": _apply_art_overrides,
    "music": _apply_music_overrides,
    "programming": _apply_programming_overrides,
    "language": _apply_language_overrides,
    "physical": _apply_physical_overrides,
}


def _apply_global_rules(
    params: LearningParameters,
    complexity_score: float,
) -> LearningParameters:
    """Apply global override rules regardless of domain.

    Rules:
    1. If technique_density > 0.7 and skill complexity > 0.7: cap at 0.7
    2. If original learning_tolerance < 0.4: enforce repetition_intensity >= 0.6
    """
    data = params.model_dump()

    # Cap technique_density if both high density and complexity
    if data["technique_density"] > 0.7 and complexity_score > 0.7:
        data["technique_density"] = 0.7

    # Enforce repetition_intensity floor for low tolerance learners
    # Note: We check against a derived metric since we don't have direct access to original ProfileVector
    # Use checkpoint_rigidity as a proxy for tolerance
    if data["checkpoint_rigidity"] < 0.4:
        data["repetition_intensity"] = max(data["repetition_intensity"], 0.6)

    return LearningParameters(**data)


def apply_skill_mapping(
    params: LearningParameters,
    domain: str,
    complexity_score: float,
    skill_modifiers: SkillModifierResult,
    skill_id: str,
) -> LearningParameters:
    """Apply skill-specific adjustments to learning parameters.

    Workflow:
    1. Apply domain-specific overrides
    2. Apply global rules
    3. Apply LLM-derived modifiers from SkillModifierResult
    4. Mark as skill-adjusted with skill_id

    Args:
        params: Base LearningParameters from ProfileVector
        domain: Skill domain (art, music, programming, language, physical, other)
        complexity_score: Skill complexity rating [0, 1]
        skill_modifiers: LLM-derived adjustments from SkillResearchObject
        skill_id: Identifier for the skill

    Returns:
        New LearningParameters instance with all adjustments applied.
        Original params object is never mutated.

    Raises:
        ValueError: If domain is not recognized
    """
    if domain not in DOMAIN_OVERRIDES:
        # For unknown domains, use identity (no overrides)
        adjusted = params.model_copy()
    else:
        # Apply domain-specific overrides
        adjusted = DOMAIN_OVERRIDES[domain](params)

    # Apply global rules
    adjusted = _apply_global_rules(adjusted, complexity_score)

    # Apply LLM-derived modifiers
    data = adjusted.model_dump()
    data["technique_density"] = _clamp(
        data["technique_density"] + skill_modifiers.technique_density_adjustment
    )
    data["repetition_intensity"] = _clamp(
        data["repetition_intensity"] + skill_modifiers.repetition_boost
    )

    # Re-apply global minimum rules after modifiers
    adjusted = LearningParameters(**data)
    adjusted = _apply_global_rules(adjusted, complexity_score)

    # Mark as skill-adjusted
    final_data = adjusted.model_dump()
    final_data["is_skill_adjusted"] = True
    final_data["skill_id"] = skill_id

    return LearningParameters(**final_data)
