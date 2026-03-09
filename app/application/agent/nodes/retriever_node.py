from sqlalchemy.orm import Session

from app.application.agent.state import AgentState
from app.infrastructure.rag.retriever import Retriever


class RetrieverNode:
    """
    Pulls relevant knowledge chunks from pgvector.
    Requires a SQLAlchemy session injected at construction.
    """

    def __init__(self, db: Session):
        self.db = db

    def run(self, state: AgentState) -> AgentState:
        if state.is_blocked:
            return state

        if not state.execution_plan or "RAG" not in state.execution_plan:
            return state

        chunks = Retriever.retrieve(state.message, db=self.db)

        if not chunks:
            state.is_blocked = True
            state.block_reason = "knowledge_not_supported"
            state.response = {"intent": "other", "message": "This feature is not supported in our yet."}
            return state

        state.rag_chunks = chunks
        return state
