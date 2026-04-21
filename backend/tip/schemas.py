from backend.shared.models import APIModel


class TipResponse(APIModel):
    available: bool
    severity: str | None = None
    text: str | None = None
    focus_step: str | None = None
