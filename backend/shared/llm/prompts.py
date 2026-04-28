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
        "Return strict JSON with exactly these keys: answer (string), source_phases (list of strings), confidence (one of: high, medium, low), caveat (string or null).\n\n"
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
        "Return strict JSON with exactly these keys: tip (string), target_step (string or null), severity (one of: minor, moderate, critical).\n\n"
        f"CONTEXT:\n{context}\n\n"
        "Tip:"
    )


def build_feasibility_prompt(profile: ProfileVector, skill: SkillTemplate) -> str:
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

Return strict JSON with exactly these keys:
- feasible (boolean)
- risk_level (one of: low, medium, high)
- blockers (list of strings)
- confidence (float 0.0-1.0)"""


def build_risk_zone_prompt(profile: ProfileVector, skill: SkillTemplate) -> str:
    return f"""Identify potential failure points for this skill based on the learner's profile:

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

Return strict JSON with exactly one key "risks" containing a list of objects. Each object must have:
- dimension (string, e.g. "Cognitive Capacity")
- type (string, e.g. "motor_constraint")
- severity (one of: low, medium, high)"""


def build_time_model_prompt(profile: ProfileVector, skill: SkillTemplate) -> str:
    phases = list(skill.structure.get("phases", {}).keys()) if skill.structure else []
    return f"""Estimate realistic timeframes for skill acquisition:

ProfileVector Time Constraint: {profile.time_constraint:.2f}
Skill Phases: {", ".join(phases) if phases else "fundamentals, intermediate, advanced"}
Skill Complexity Score: {skill.complexity_score:.3f}

Return strict JSON with exactly these keys:
- estimated_weeks (integer)
- hours_per_phase (dictionary where keys are phase names and values are floats)
- confidence (float 0.0-1.0)"""


def build_skill_modifier_prompt(profile: ProfileVector, skill: SkillTemplate) -> str:
    return f"""Derive learning parameter adjustments (fine-tuning) for this skill:

Learner Profile:
- Cognitive Capacity: {profile.cognitive_capacity:.2f}
- Motor Baseline: {profile.motor_baseline:.2f}
- Learning Tolerance: {profile.learning_tolerance:.2f}

Skill Details:
- Domain: {skill.domain}
- Complexity Score: {skill.complexity_score:.3f}

Return strict JSON with exactly these keys:
- technique_density_adjustment (float between -0.3 and 0.3)
- repetition_boost (float between -0.3 and 0.3)
- notes (string explanation)

CRITICAL: The adjustments MUST be between -0.3 and 0.3. Use 0.0 for no change."""


def build_skill_analysis_prompt(skill_name: str, context: dict) -> str:
    import json
    return f"""Analyze the following search data for the skill: "{skill_name}".

RESEARCH DATA:
{json.dumps(context, indent=2)}

TASK:
1. Analyze the skill's complexity and requirements based on the data.
2. Identify gaps in the data that require user input (e.g., goals, constraints, prior experience).
3. Generate a set of 3-5 high-impact questions to fill these gaps.

CONSTRAINTS:
- Return ONLY valid JSON.
- Use temperature 0.0.
- Questions must have types: "single_select", "multi_select", "numeric", or "slider".
- Complexity score must be between 0.0 and 1.0.

REQUIRED JSON SCHEMA:
{{
  "analysis": {{
    "skill_name": "string",
    "complexity_score": float,
    "prerequisite_gaps": ["string"],
    "estimated_phases": ["string"],
    "common_failure_modes": ["string"]
  }},
  "questions": [
    {{
      "id": "string",
      "text": "string",
      "type": "single_select | multi_select | numeric | slider",
      "options": ["string"],
      "min": number,
      "max": number,
      "step": number
    }}
  ]
}}
"""

