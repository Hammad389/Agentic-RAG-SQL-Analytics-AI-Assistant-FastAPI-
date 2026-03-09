from dotenv import load_dotenv
load_dotenv()  # ← must be first, before any app import touches os.getenv()

from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.application.services.ai_agent_service import ChatService
from app.database import get_db, init_db
from app.infrastructure.ai.fastapi_chat_repository import FastAPIChatRepository


# ─────────────────────────────────────────────────────
# Lifespan: DB init on startup
# ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Agentic Rag",
    description="Conversational AI agent — no authentication required.",
    version="2.0.0",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    success: bool
    intent: Optional[list] = None
    execution_plan: Optional[list] = None
    data: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None


# ─────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────
@app.post("/chat/", response_model=ChatResponse, summary="Send a message to the AI agent")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    service = ChatService(db=db)
    result = service.ai_agent_handler(message=request.message)
    return result


@app.post("/chat/with-history/", response_model=ChatResponse, summary="Chat with conversation persistence")
async def chat_with_history(request: ChatRequest, db: Session = Depends(get_db)):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    repo = FastAPIChatRepository(db=db)
    service = ChatService(db=db, repo=repo)
    result = service.ai_agent_handler(message=request.message)
    return result


@app.get("/health/", summary="Health check")
async def health():
    return {"status": "ok"}


# ─────────────────────────────────────────────────────
# Knowledge indexing endpoint (admin use)
# ─────────────────────────────────────────────────────
@app.post("/admin/index-knowledge/", summary="Index knowledge base documents")
async def index_knowledge(db: Session = Depends(get_db)):
    from app.application.rag.chunker import TextChunker
    from app.infrastructure.rag.document_loader import DocumentLoader
    from app.infrastructure.rag.indexer import KnowledgeIndexer

    loader = DocumentLoader()
    chunker = TextChunker()
    indexer = KnowledgeIndexer(db=db)

    documents = loader.load_documents()
    if not documents:
        return {"status": "no_documents_found", "indexed": 0}

    all_chunks = []
    for doc in documents:
        chunks = chunker.chunk_text(
            text=doc["content"],
            metadata={
                "title": doc["title"],
                "source_type": doc["source_type"],
                "file_name": doc["file_name"],
            },
        )
        all_chunks.extend(chunks)

    count = indexer.index_chunks(all_chunks)
    return {"status": "success", "documents": len(documents), "indexed": count}
