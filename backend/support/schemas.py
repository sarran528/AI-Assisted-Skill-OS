from backend.shared.models import APIModel


class DoubtAskRequest(APIModel):
    skill_id: str
    phase: str
    technique_id: str
    question: str


class DoubtAskResponse(APIModel):
    answer: str
    confidence: str
    caveat: str | None = None
    sources_used: int = 0


class SupportResourceItem(APIModel):
    id: str
    doc_type: str
    snippet: str
    relevance: float


class SupportResourcesResponse(APIModel):
    items: list[SupportResourceItem]
