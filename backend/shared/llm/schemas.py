from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator


class FeasibilityResult(BaseModel):
    feasible: bool
    risk_level: Literal["low", "medium", "high"]
    blockers: list[str] = []
    confidence: float


class RiskItem(BaseModel):
    dimension: str
    type: str
    severity: Literal["low", "medium", "high"]


class RiskZoneResult(BaseModel):
    risks: list[RiskItem] = []


class TimeModelResult(BaseModel):
    estimated_weeks: int
    hours_per_phase: dict[str, float] = {}
    confidence: float


class SkillModifierResult(BaseModel):
    technique_density_adjustment: float
    repetition_boost: float
    notes: str = ""


DEFAULT_FEASIBILITY = FeasibilityResult(
    feasible=True,
    risk_level="medium",
    blockers=[],
    confidence=0.5,
)

DEFAULT_RISK_ZONES = RiskZoneResult(risks=[])

DEFAULT_TIME_MODEL = TimeModelResult(
    estimated_weeks=12,
    hours_per_phase={},
    confidence=0.3,
)

DEFAULT_SKILL_MODIFIERS = SkillModifierResult(
    technique_density_adjustment=0.0,
    repetition_boost=0.0,
    notes="Fallback defaults",
)


class DoubtAnswerSchema(BaseModel):
    answer: str
    source_phases: list[str]
    confidence: Literal["high", "medium", "low"]
    caveat: str | None = None


class TipSchema(BaseModel):
    tip: str
    target_step: str | None
    severity: Literal["minor", "moderate", "critical"]

    @field_validator("tip")
    @classmethod
    def tip_max_words(cls, value: str) -> str:
        if len(value.split()) > 100:
            raise ValueError("tip must be 100 words or fewer")
        return value
