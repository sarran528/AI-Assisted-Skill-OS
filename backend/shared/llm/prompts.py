from __future__ import annotations

from backend.assessment.profile_vector import ProfileVector
from backend.shared.db.models.skill_template import SkillTemplate


def build_doubt_prompt(
    context: str,
    question: str,
    skill_id: str,
    phase: str | None,
    technique: str | None,
) -> str:
    return (
        f"You are a learning assistant for the skill: {skill_id}.\n"
        f"The learner is currently in the {phase or 'unknown'} phase, working on: {technique or 'unknown'}.\n\n"
        "Use ONLY the following reference material to answer the question.\n"
        "Do not use any knowledge outside of the provided context.\n"
        "If the context does not contain enough information to answer, say so clearly.\n\n"
        "Return strict JSON with keys: answer, source_phases, confidence, caveat.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION:\n{question}\n\n"
        "Respond with a concise, specific answer in 2-4 sentences. No preamble."
    )


def build_tip_prompt(context: str, technique_id: str, failure_type: str, attempt_number: int) -> str:
    return (
        f"You are providing a targeted correction for a learner who is failing at: {technique_id}.\n"
        f"Failure type: {failure_type}\n"
        f"Number of failed attempts: {attempt_number}\n\n"
        "Use ONLY the following reference material.\n"
        "Provide ONE specific, actionable correction. Maximum 2 sentences.\n"
        "Do not explain why this matters. Do not provide encouragement. Just the correction.\n"
        "Return strict JSON with keys: tip, target_step, severity.\n\n"
        f"CONTEXT:\n{context}\n\n"
        "Tip:"
    )


def build_feasibility_prompt(profile: ProfileVector, skill: SkillTemplate) -> str:
    """
    Build prompt for feasibility analysis.

    Args:
        profile: User's ProfileVector
        skill: Target skill template

    Returns:
        Complete feasibility analysis prompt
    """
    return f"""Evaluate if a learner with the following profile can feasibly acquire this skill:

ProfileVector Dimensions:
- Cognitive Capacity: {profile.cognitive_capacity:.2f}
- Attention Stability: {profile.attention_stability:.2f}
- Learning Tolerance: {profile.learning_tolerance:.2f}
- Motor Baseline: {profile.motor_baseline:.2f}
- Stress Resilience: {profile.stress_resilience:.2f}
- Time Constraint: {profile.time_constraint:.2f}

Skill Details:
- Domain: {skill.domain}
- Complexity Score: {skill.complexity_score:.3f}
- Name: {skill.name}

Return a JSON response evaluating feasibility considering the learner's constraints."""


def build_risk_zone_prompt(profile: ProfileVector, skill: SkillTemplate) -> str:
    """
    Build prompt for risk zone detection.

    Args:
        profile: User's ProfileVector
        skill: Target skill template

    Returns:
        Complete risk zone detection prompt
    """
    return f"""Identify which dimensions of the learner's profile represent potential failure points for this skill:

ProfileVector Dimensions:
- Cognitive Capacity: {profile.cognitive_capacity:.2f}
- Attention Stability: {profile.attention_stability:.2f}
- Learning Tolerance: {profile.learning_tolerance:.2f}
- Motor Baseline: {profile.motor_baseline:.2f}
- Stress Resilience: {profile.stress_resilience:.2f}
- Time Constraint: {profile.time_constraint:.2f}

Skill Details:
- Domain: {skill.domain}
- Complexity Score: {skill.complexity_score:.3f}

Return a JSON response identifying risks specific to this skill-profile combination."""


def build_time_model_prompt(profile: ProfileVector, skill: SkillTemplate) -> str:
    """
    Build prompt for time modeling.

    Args:
        profile: User's ProfileVector
        skill: Target skill template

    Returns:
        Complete time modeling prompt
    """
    phases = list(skill.structure.get("phases", {}).keys()) if skill.structure else []
    return f"""Estimate realistic timeframes for skill acquisition:

ProfileVector Time Constraint: {profile.time_constraint:.2f}
Skill Phases: {", ".join(phases) if phases else "fundamentals, intermediate, advanced"}
Skill Complexity Score: {skill.complexity_score:.3f}

Return a JSON response with total weeks and hours per phase estimates."""


def build_skill_modifier_prompt(profile: ProfileVector, skill: SkillTemplate) -> str:
    """
    Build prompt for skill modifier derivation.

    Args:
        profile: User's ProfileVector
        skill: Target skill template

    Returns:
        Complete skill modifier prompt
    """
    return f"""Derive learning parameter adjustments specific to this skill:

Learner Profile:
- Cognitive Capacity: {profile.cognitive_capacity:.2f}
- Motor Baseline: {profile.motor_baseline:.2f}
- Learning Tolerance: {profile.learning_tolerance:.2f}

Skill Details:
- Domain: {skill.domain}
- Complexity Score: {skill.complexity_score:.3f}

Return a JSON response with technique_density_adjustment and repetition_boost modifiers."""
