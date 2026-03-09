from sqlalchemy.orm import Session

from app.infrastructure.ai.embedding_service import EmbeddingService
from app.models.rag_document import KnowledgeChunk


class KnowledgeIndexer:
    """
    Indexes document chunks into the knowledge_chunks table.
    Requires a SQLAlchemy Session.
    """

    def __init__(self, db: Session):
        self.db = db

    def index_chunks(self, chunks: list) -> int:
        """
        Embeds and saves chunks. Returns count of indexed chunks.
        """
        count = 0
        for chunk in chunks:
            embedding = EmbeddingService.embed(chunk["content"])
            db_chunk = KnowledgeChunk(
                content=chunk["content"],
                embedding=embedding,
                metadata_=chunk.get("metadata", {}),
            )
            self.db.add(db_chunk)
            count += 1

        self.db.commit()
        return count
