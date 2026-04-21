from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models import Evidence

UPLOAD_DIR = Path("backend/.uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def create_evidence_record(
    db_session: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    checkpoint_id: str,
    evidence_type: str,
    file: UploadFile,
) -> Evidence:
    content = await file.read()
    size_bytes = len(content)
    artifact_key = f"{user_id}/{session_id}/{checkpoint_id}/{uuid4()}-{file.filename}"

    disk_path = UPLOAD_DIR / artifact_key
    disk_path.parent.mkdir(parents=True, exist_ok=True)
    disk_path.write_bytes(content)

    payload = {
        "filename": file.filename,
        "artifact_key": artifact_key,
    }

    await db_session.execute(
        insert(Evidence).values(
            user_id=user_id,
            session_id=session_id,
            checkpoint_id=checkpoint_id,
            type=evidence_type,
            payload=payload,
            artifact_url=f"/local-evidence/{artifact_key}",
            artifact_key=artifact_key,
            mime_type=file.content_type,
            file_size_bytes=size_bytes,
            validated=False,
        )
    )
    await db_session.commit()

    result = await db_session.execute(
        select(Evidence)
        .where(Evidence.user_id == user_id)
        .where(Evidence.session_id == session_id)
        .where(Evidence.checkpoint_id == checkpoint_id)
        .order_by(Evidence.created_at.desc())
    )
    return result.scalars().first()


async def list_session_evidence(
    db_session: AsyncSession,
    session_id: UUID,
    user_id: UUID,
) -> list[Evidence]:
    result = await db_session.execute(
        select(Evidence)
        .where(Evidence.session_id == session_id)
        .where(Evidence.user_id == user_id)
        .order_by(Evidence.created_at.desc())
    )
    return list(result.scalars().all())
