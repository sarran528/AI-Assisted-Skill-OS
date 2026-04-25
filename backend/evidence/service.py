from __future__ import annotations

import hashlib
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.audit import log_audit_event
from backend.shared.db.repositories.evidence_repository import EvidenceRepository
from backend.shared.storage.uploader import upload_evidence_file


async def upload_evidence(
    db: AsyncSession,
    file: UploadFile,
    session_id: UUID,
    checkpoint_id: str,
    user_id: UUID,
    evidence_type: str,
):
    file_bytes = await file.read()
    object_key, artifact_url, mime_type = await upload_evidence_file(
        file_bytes=file_bytes,
        original_filename=file.filename or "evidence.bin",
        session_id=session_id,
        checkpoint_id=checkpoint_id,
        user_id=user_id,
    )

    checksum = hashlib.sha256(file_bytes).hexdigest()
    record = await EvidenceRepository.create(
        db,
        {
            "session_id": session_id,
            "user_id": user_id,
            "checkpoint_id": checkpoint_id,
            "type": evidence_type,
            "payload": {"checksum_sha256": checksum},
            "artifact_url": artifact_url,
            "artifact_key": object_key,
            "mime_type": mime_type,
            "file_size_bytes": len(file_bytes),
            "validated": False,
        },
    )

    await log_audit_event(
        db,
        user_id=str(user_id),
        action="evidence.uploaded",
        entity_type="evidence",
        entity_id=str(record.id),
        ip_address=None,
        metadata={"checkpoint_id": checkpoint_id, "mime_type": mime_type},
    )
    return record


async def list_evidence_for_session(db: AsyncSession, session_id: UUID, user_id: UUID):
    return await EvidenceRepository.get_by_session_and_user(db, session_id, user_id)
