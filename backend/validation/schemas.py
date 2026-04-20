from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel


@dataclass
class ValidationResult:
    passed: bool
    threshold: float | None
    actual: float | str | None
    reason: str
    evidence_type: str

    def to_dict(self) -> dict:
        return asdict(self)


class CheckpointValidateRequest(BaseModel):
    session_id: UUID
    checkpoint_id: str
