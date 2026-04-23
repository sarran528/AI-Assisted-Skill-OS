from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import AuthContext, get_current_user
from backend.evidence.schemas import EvidenceListItem, EvidenceListResponse, EvidenceUploadResponse
from backend.evidence.service import list_evidence_for_session, upload_evidence
from backend.shared.db.session import get_db_session

router = APIRouter()

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_MIME_PREFIXES = ("image/",)
ALLOWED_MIME_TYPES = {"application/pdf", "text/plain", "video/mp4"}

def validate_evidence_file(file: UploadFile):
    if file.size and file.size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of 50MB."
        )
    
    content_type = file.content_type or ""
    is_valid_type = any(content_type.startswith(prefix) for prefix in ALLOWED_MIME_PREFIXES) or content_type in ALLOWED_MIME_TYPES
    if not is_valid_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {content_type}. Allowed types: image/*, application/pdf, text/plain, video/mp4."
        )

@router.post("/upload", response_model=EvidenceUploadResponse)
async def upload_evidence_route(
    file: UploadFile = File(...),
    session_id: UUID = Form(...),
    checkpoint_id: str = Form(...),
    evidence_type: str = Form(...),
    db_session: AsyncSession = Depends(get_db_session),
    current_user: AuthContext = Depends(get_current_user),
) -> EvidenceUploadResponse:
    validate_evidence_file(file)
    record = await upload_evidence(
        db_session,
        file,
        session_id,
        checkpoint_id,
        current_user.user.id,
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


@router.get("/{session_id}", response_model=EvidenceListResponse)
async def list_evidence_route(
    session_id: UUID,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: AuthContext = Depends(get_current_user),
) -> EvidenceListResponse:
    records = await list_evidence_for_session(db_session, session_id, current_user.user.id)
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
