from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.evidence.schemas import EvidenceListItem, EvidenceListResponse, EvidenceUploadResponse
from backend.evidence.service import list_evidence_for_session, upload_evidence
from backend.shared.db.session import get_db_session

router = APIRouter()


@router.post("/upload", response_model=EvidenceUploadResponse)
async def upload_evidence_route(
    file: UploadFile = File(...),
    session_id: UUID = Form(...),
    checkpoint_id: str = Form(...),
    evidence_type: str = Form(...),
    db_session: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
) -> EvidenceUploadResponse:
    record = await upload_evidence(
        db_session,
        file,
        session_id,
        checkpoint_id,
        current_user["user"].id,
        evidence_type,
    )
    return EvidenceUploadResponse(
        evidence_id=record.id,
        checkpoint_id=record.checkpoint_id,
        artifact_url=record.artifact_url or "",
        mime_type=record.mime_type or "",
        file_size_bytes=record.file_size_bytes or 0,
        validated=record.validated,
    )


@router.get("/session/{session_id}", response_model=EvidenceListResponse)
async def list_evidence_route(
    session_id: UUID,
    db_session: AsyncSession = Depends(get_db_session),
) -> EvidenceListResponse:
    records = await list_evidence_for_session(db_session, session_id)
    return EvidenceListResponse(
        items=[
            EvidenceListItem(
                evidence_id=item.id,
                checkpoint_id=item.checkpoint_id,
                evidence_type=item.type,
                artifact_url=item.artifact_url,
                validated=item.validated,
            )
            for item in records
        ]
    )
