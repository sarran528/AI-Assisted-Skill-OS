from datetime import datetime
from uuid import UUID

from backend.shared.models import APIModel


class EvidenceUploadResponse(APIModel):
    evidence_id: UUID
    session_id: UUID
    checkpoint_id: str
    artifact_url: str | None
    mime_type: str | None
    file_size_bytes: int
    validated: bool
    created_at: datetime


class EvidenceListItem(APIModel):
    evidence_id: UUID
    checkpoint_id: str
    artifact_url: str | None
    mime_type: str | None
    validated: bool
    created_at: datetime


class EvidenceListResponse(APIModel):
    session_id: UUID
    items: list[EvidenceListItem]
