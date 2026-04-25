import uuid

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models import AuditLog


async def log_audit_event(
    db_session: AsyncSession,
    *,
    user_id: str | None,
    action: str,
    entity_type: str | None,
    entity_id: str | None,
    ip_address: str | None,
    metadata: dict | None = None,
) -> None:
    user_uuid = None
    entity_uuid = None

    if user_id:
        try:
            user_uuid = str(uuid.UUID(str(user_id)))
        except ValueError:
            user_uuid = None

    if entity_id:
        try:
            entity_uuid = str(uuid.UUID(str(entity_id)))
        except ValueError:
            entity_uuid = None

    await db_session.execute(
        insert(AuditLog).values(
            user_id=user_uuid,
            action=action,
            entity_type=entity_type,
            entity_id=entity_uuid,
            ip_address=ip_address,
                metadata_=metadata or {},
        )
    )
    await db_session.commit()
