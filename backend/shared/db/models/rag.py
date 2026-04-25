from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from backend.shared.db.base import Base


class RagChunk(Base):
    __tablename__ = "rag_chunks"
    __table_args__ = (
        UniqueConstraint("skill_id", "source_url", "chunk_index", name="uq_rag_chunks_skill_source_chunk"),
    )

    id = Column(String(36), primary_key=True, server_default=text("uuid_generate_v4()"))
    skill_id = Column(String(64), nullable=False)
    phase = Column(String(64), nullable=True)
    technique_id = Column(String(64), nullable=True)
    doc_type = Column(String(32), nullable=False)
    source_url = Column(Text, nullable=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=False)
    model_name = Column(String(64), nullable=False)
    token_count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class RagConfig(Base):
    __tablename__ = "rag_config"

    id = Column(Integer, primary_key=True, server_default=text("1"))
    model_name = Column(String(64), nullable=False)
    model_version = Column(String(32), nullable=False)
    dimension = Column(Integer, nullable=False)
    chunk_size = Column(Integer, nullable=False, server_default=text("512"))
    chunk_overlap = Column(Integer, nullable=False, server_default=text("64"))
    last_indexed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
