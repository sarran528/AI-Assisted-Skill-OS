from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator


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
