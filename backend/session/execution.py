from __future__ import annotations

from dataclasses import dataclass

from backend.shared.db.models import LearningParameter, Session


@dataclass(slots=True)
class SessionResult:
    passed: bool
    failure_reason: str | None


def should_generate_tip(
    result: SessionResult,
    session: Session,
    params: LearningParameter,
) -> bool:
    if result.passed:
        return False

    if int(session.attempt_number) >= 2:
        return True

    metrics = session.metrics_captured or {}
    retry_count = int(metrics.get("retry_count", metrics.get("retry", 0)) or 0)
    if retry_count > int(params.retry_limit):
        return True

    performance_decay = float(metrics.get("performance_decay", 0) or 0)
    if performance_decay > 0.5:
        return True

    return False
