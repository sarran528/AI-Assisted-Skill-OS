"""Skill intelligence computation engine."""
from datetime import datetime
from typing import Any
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from backend.assessment.profile_vector import ProfileVector
from backend.shared.db.models.skill_template import SkillTemplate
from backend.shared.llm.schemas import (
    FeasibilityResult,
    RiskZoneResult,
    SkillModifierResult,
    TimeModelResult,
)


class SkillAnalysis(BaseModel):
    skill_name: str
    complexity_score: float
    prerequisite_gaps: list[str]
    estimated_phases: list[str]
    common_failure_modes: list[str]


class SkillQuestion(BaseModel):
    id: str
    text: str
    type: Literal["single_select", "multi_select", "numeric", "slider"]
    options: list[str] | None = None
    min: float | None = None
    max: float | None = None
    step: float | None = None


class SkillAnalysisResponse(BaseModel):
    analysis: SkillAnalysis
    questions: list[SkillQuestion]


class SkillResearchObject(BaseModel):
    """Complete intelligence package for a skill-profile combination."""

    skill_id: str = Field(..., description="Skill identifier")
    user_id: UUID = Field(..., description="User who generated this research")
    profile_version: int = Field(..., description="ProfileVector version used")
    feasibility: FeasibilityResult = Field(..., description="Feasibility analysis result")
    risk_zones: RiskZoneResult = Field(..., description="Risk zone detection result")
    time_model: TimeModelResult = Field(..., description="Time modeling result")
    skill_modifiers: SkillModifierResult = Field(..., description="Skill-specific modifiers")
    confidence_bias: float = Field(..., ge=-1.0, le=1.0, description="User's confidence bias")
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # Derived convenience fields
    is_feasible: bool = Field(..., description="Whether skill acquisition is feasible")
    estimated_weeks: int = Field(..., ge=1, description="Total weeks to complete")
    overall_risk: Literal["low", "medium", "high"] = Field(
        ..., description="Overall risk level"
    )
    user_goal: str | None = Field(default=None, description="User target goal context")
    difficulty_modifier: float = Field(default=1.0, ge=0.5, le=2.0)
    phases: list[str] = Field(default_factory=list)
    techniques: list[str] = Field(default_factory=list)
    checkpoints: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    estimated_total_hours: int | None = Field(default=None, ge=1)
    user_answers: dict[str, Any] | None = Field(default=None)

    @classmethod
    def from_llm_results(
        cls,
        skill_id: str,
        user_id: UUID,
        profile_version: int,
        feasibility: FeasibilityResult,
        risk_zones: RiskZoneResult,
        time_model: TimeModelResult,
        skill_modifiers: SkillModifierResult,
        confidence_bias: float,
        user_goal: str | None = None,
        difficulty_modifier: float = 1.0,
        phases: list[str] | None = None,
        techniques: list[str] | None = None,
        checkpoints: list[str] | None = None,
        prerequisites: list[str] | None = None,
        estimated_total_hours: int | None = None,
        user_answers: dict[str, Any] | None = None,
    ) -> "SkillResearchObject":
        """Assemble SkillResearchObject from LLM results with derived fields."""
        return cls(
            skill_id=skill_id,
            user_id=user_id,
            profile_version=profile_version,
            feasibility=feasibility,
            risk_zones=risk_zones,
            time_model=time_model,
            skill_modifiers=skill_modifiers,
            confidence_bias=confidence_bias,
            generated_at=datetime.utcnow(),
            is_feasible=feasibility.feasible,
            estimated_weeks=max(1, round(float(time_model.estimated_weeks) * float(difficulty_modifier))),
            overall_risk=feasibility.risk_level,
            user_goal=user_goal,
            difficulty_modifier=difficulty_modifier,
            phases=phases or [],
            techniques=techniques or [],
            checkpoints=checkpoints or [],
            prerequisites=prerequisites or [],
            estimated_total_hours=estimated_total_hours,
            user_answers=user_answers,
        )


async def compute_skill_research(
    profile: ProfileVector,
    baseline_state: "BaselineSkillState",  # type: ignore  # noqa: F821
    template: SkillTemplate,
    user_goal: str | None = None,
    difficulty_modifier: float = 1.0,
    user_answers: dict[str, Any] | None = None,
    template_constants: dict[str, Any] | None = None,
) -> SkillResearchObject:
    """
    Orchestrate four sequential LLM calls to produce SkillResearchObject.

    Makes calls in order:
    1. Feasibility analysis (profile + skill → feasibility)
    2. Risk zone detection (ProfileVector + domain → risks)
    3. Time modeling (parameters + phases → timeline)
    4. Skill modifier derivation (domain + complexity → adjustments)

    Args:
        profile: User's ProfileVector
        baseline_state: BaselineSkillState from grounding probes
        template: Active skill template

    Returns:
        Assembled SkillResearchObject with all four LLM results

    Raises:
        SystemError: If LLM calls fail unrecoverably
    """
    # Import here to avoid circular imports
    from backend.shared.llm.gateway import llm_call
    from backend.shared.llm.prompts import (
        build_feasibility_prompt,
        build_risk_zone_prompt,
        build_skill_modifier_prompt,
        build_time_model_prompt,
    )
    from backend.shared.llm.schemas import (
        DEFAULT_FEASIBILITY,
        DEFAULT_RISK_ZONES,
        DEFAULT_SKILL_MODIFIERS,
        DEFAULT_TIME_MODEL,
    )

    # Call 1: Feasibility analysis
    feasibility = await llm_call(
        prompt=build_feasibility_prompt(profile, template),
        system_prompt="You are the SkillOS intelligence engine. Respond ONLY with valid JSON matching the provided schema. No explanation, no markdown, no preamble.",
        response_schema=FeasibilityResult,
        fallback=DEFAULT_FEASIBILITY,
        temperature=0.0,
    )

    # Call 2: Risk zone detection
    risk_zones = await llm_call(
        prompt=build_risk_zone_prompt(profile, template),
        system_prompt="You are the SkillOS intelligence engine. Respond ONLY with valid JSON matching the provided schema. No explanation, no markdown, no preamble.",
        response_schema=RiskZoneResult,
        fallback=DEFAULT_RISK_ZONES,
        temperature=0.0,
    )

    # Call 3: Time modeling
    time_model = await llm_call(
        prompt=build_time_model_prompt(profile, template),
        system_prompt="You are the SkillOS intelligence engine. Respond ONLY with valid JSON matching the provided schema. No explanation, no markdown, no preamble.",
        response_schema=TimeModelResult,
        fallback=DEFAULT_TIME_MODEL,
        temperature=0.0,
    )

    # Call 4: Skill modifier derivation
    skill_modifiers = await llm_call(
        prompt=build_skill_modifier_prompt(profile, template),
        system_prompt="You are the SkillOS intelligence engine. Respond ONLY with valid JSON matching the provided schema. No explanation, no markdown, no preamble.",
        response_schema=SkillModifierResult,
        fallback=DEFAULT_SKILL_MODIFIERS,
        temperature=0.0,
    )

    # Assemble final object with derived fields
    return SkillResearchObject.from_llm_results(
        skill_id=template.skill_id,
        user_id=baseline_state.user_id,
        profile_version=profile.version,
        feasibility=feasibility,
        risk_zones=risk_zones,
        time_model=time_model,
        skill_modifiers=skill_modifiers,
        confidence_bias=baseline_state.confidence_bias,
        user_goal=user_goal,
        difficulty_modifier=difficulty_modifier,
        phases=list((template_constants or {}).get("phases", [])),
        techniques=list((template_constants or {}).get("techniques", [])),
        checkpoints=list((template_constants or {}).get("checkpoints", [])),
        prerequisites=list((template_constants or {}).get("prerequisites", [])),
        estimated_total_hours=(template_constants or {}).get("estimated_total_hours"),
        user_answers=user_answers,
    )


async def analyze_skill_context(skill_name: str, context: dict[str, Any]) -> SkillAnalysisResponse:
    """Stage 4: LLM + Agentic AI analysis of skill context."""
    from backend.shared.llm.gateway import llm_call
    from backend.shared.llm.prompts import build_skill_analysis_prompt

    result = await llm_call(
        prompt=build_skill_analysis_prompt(skill_name, context),
        system_prompt="You are the SkillOS intelligence engine. Respond ONLY with valid JSON matching the provided schema.",
        response_schema=SkillAnalysisResponse,
        temperature=0.0,
    )
    
    if not result:
        # Fallback if LLM fails
        return SkillAnalysisResponse(
            analysis=SkillAnalysis(
                skill_name=skill_name,
                complexity_score=0.5,
                prerequisite_gaps=[],
                estimated_phases=["fundamentals", "intermediate", "advanced"],
                common_failure_modes=[]
            ),
            questions=[
                SkillQuestion(
                    id="experience",
                    text="What is your prior experience with this skill?",
                    type="slider",
                    min=1,
                    max=5,
                    step=1
                )
            ]
        )
    return result
