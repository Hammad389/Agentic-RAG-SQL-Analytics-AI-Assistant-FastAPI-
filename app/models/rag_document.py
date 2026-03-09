from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.database import Base


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    embedding = Column(Vector(384))
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<KnowledgeChunk(id={self.id}, content={self.content[:50]!r})>"
