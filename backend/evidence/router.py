from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.evidence.schemas import EvidenceListItem, EvidenceListResponse, EvidenceUploadResponse
from backend.evidence.service import create_evidence_record, list_session_evidence
from backend.auth.dependencies import get_current_user
from backend.shared.db.session import get_db_session
from backend.shared.rate_limit import limiter

router = APIRouter()


@router.post("/upload", response_model=EvidenceUploadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
async def upload_evidence(
    request: Request,
    file: UploadFile = File(...),
    session_id: UUID = Form(...),
    checkpoint_id: str = Form(...),
    evidence_type: str = Form("artifact"),
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> EvidenceUploadResponse:
    evidence = await create_evidence_record(
        db_session=db_session,
        user_id=current_user["user"].id,
        session_id=session_id,
        checkpoint_id=checkpoint_id,
        evidence_type=evidence_type,
        file=file,
    )

    return EvidenceUploadResponse(
        evidence_id=evidence.id,
        session_id=evidence.session_id,
        checkpoint_id=evidence.checkpoint_id,
        artifact_url=evidence.artifact_url,
        mime_type=evidence.mime_type,
        file_size_bytes=evidence.file_size_bytes or 0,
        validated=bool(evidence.validated),
        created_at=evidence.created_at,
    )


@router.get("/session/{session_id}", response_model=EvidenceListResponse)
async def get_session_evidence(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> EvidenceListResponse:
    records = await list_session_evidence(
        db_session=db_session,
        session_id=session_id,
        user_id=current_user["user"].id,
    )
    return EvidenceListResponse(
        session_id=session_id,
        items=[
            EvidenceListItem(
                evidence_id=record.id,
                checkpoint_id=record.checkpoint_id,
                artifact_url=record.artifact_url,
                mime_type=record.mime_type,
                validated=bool(record.validated),
                created_at=record.created_at,
            )
            for record in records
        ],
    )
