"""ORM model for skill research objects."""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UUID as SQLALCHEMY_UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.db.base import Base


class SkillResearchObjectModel(Base):
    """Persisted skill research object with full intelligence package."""

    __tablename__ = "skill_research_objects"

    id: Mapped[UUID] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        SQLALCHEMY_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    profile_version: Mapped[int] = mapped_column(nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, server_default="now()"
    )

    def __repr__(self) -> str:
        return f"<SkillResearchObject {self.skill_id} user={self.user_id}>"
