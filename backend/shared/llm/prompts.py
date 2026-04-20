"""LLM prompt templates for skill intelligence engine."""
from backend.assessment.profile_vector import ProfileVector
from backend.shared.db.models.skill_template import SkillTemplate


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
