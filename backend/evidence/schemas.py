from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class EvidenceUploadResponse(BaseModel):
    evidence_id: UUID
    checkpoint_id: str
    artifact_url: str
    mime_type: str
    file_size_bytes: int
    validated: bool


class EvidenceListItem(BaseModel):
    evidence_id: UUID
    checkpoint_id: str
    evidence_type: str
    artifact_url: str | None
    validated: bool


class EvidenceListResponse(BaseModel):
    items: list[EvidenceListItem]
