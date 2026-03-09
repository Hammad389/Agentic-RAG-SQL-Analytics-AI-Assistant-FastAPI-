from typing import List

from pgvector.sqlalchemy import Vector
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.application.rag.token_estimator import TokenEstimator
from app.infrastructure.ai.embedding_service import EmbeddingService
from app.models.rag_document import KnowledgeChunk


class Retriever:
    """
    Production-grade RAG retriever using SQLAlchemy + pgvector.

    Features:
    - Hard top_k
    - Distance threshold
    - Token budgeting
    - Context-safe output
    """

    TOP_K = 6
    FINAL_TOP_K = 3
    MAX_CONTEXT_TOKENS = 800
    MAX_DISTANCE = 0.35

    @classmethod
    def retrieve(cls, query: str, db: Session) -> List[str]:
        # 1) Embed query
        query_embedding = EmbeddingService.embed(query)

        # 2) Vector search via pgvector cosine distance
        # pgvector SQLAlchemy: use the <=> operator via .cosine_distance()
        candidates = (
            db.query(
                KnowledgeChunk,
                KnowledgeChunk.embedding.cosine_distance(query_embedding).label("distance"),
            )
            .order_by("distance")
            .limit(cls.TOP_K)
            .all()
        )

        # 3) Filter by semantic distance threshold
        filtered = [chunk for chunk, distance in candidates if distance is not None and distance <= cls.MAX_DISTANCE]

        # Fallback: if nothing under threshold, use raw top_k
        if not filtered:
            filtered = [chunk for chunk, _ in candidates]

        # 4) Token budgeting
        selected_chunks = []
        total_tokens = 0

        for chunk in filtered:
            content = chunk.content.strip()
            token_count = TokenEstimator.estimate(content)

            if total_tokens + token_count > cls.MAX_CONTEXT_TOKENS:
                break

            selected_chunks.append(content)
            total_tokens += token_count

            if len(selected_chunks) >= cls.FINAL_TOP_K:
                break

        return selected_chunks
