import uuid
from datetime import datetime
from typing import List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text, ForeignKey, Enum as SAEnum, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin, TimestampMixin
from app.models.enums import SourceType

EMBEDDING_DIM = 1536  # text-embedding-3-small


class Source(UUIDPKMixin, TimestampMixin, Base):
    """A retrieved external source (article, report, company page, etc.)."""

    __tablename__ = "sources"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("research_jobs.id"))
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    title: Mapped[str] = mapped_column(String(500), default="")
    publisher: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType), default=SourceType.web)
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_demo: Mapped[bool] = mapped_column(default=False)

    documents: Mapped[List["Document"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class Document(UUIDPKMixin, TimestampMixin, Base):
    """Extracted + cleaned full text of a source, prior to chunking."""

    __tablename__ = "documents"

    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id"))
    raw_text: Mapped[str] = mapped_column(Text, default="")
    cleaned_text: Mapped[str] = mapped_column(Text, default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)

    source: Mapped["Source"] = relationship(back_populates="documents")
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(UUIDPKMixin, TimestampMixin, Base):
    """A chunk of a document with its embedding, for RAG retrieval."""

    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"))
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)

    document: Mapped["Document"] = relationship(back_populates="chunks")
