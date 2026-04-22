from __future__ import annotations

from datetime import datetime
from uuid import UUID

from backend.shared.models import APIModel


class ProfileVectorResponse(APIModel):
    id: UUID
    user_id: UUID
    version: int
    cognitive_capacity: float
    attention_stability: float
    learning_tolerance: float
    motor_baseline: float
    stress_resilience: float
    time_constraint: float
    raw_signals: dict
    created_at: datetime

    model_config = {
        **APIModel.model_config,
        "from_attributes": True,
    }
