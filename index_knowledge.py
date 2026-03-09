"""
index_knowledge.py
==================
Drop this file in your project root (next to main.py) and run it once
whenever you add or update files in knowledge_base/.

Usage:
    python index_knowledge.py              # append new chunks
    python index_knowledge.py --fresh      # wipe everything and re-index
"""

import argparse
import sys
from pathlib import Path

# Make sure project root is on sys.path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Load .env BEFORE any app code runs
from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal, init_db
from app.application.rag.chunker import TextChunker
from app.infrastructure.rag.document_loader import DocumentLoader
from app.infrastructure.rag.indexer import KnowledgeIndexer
from app.models.rag_document import KnowledgeChunk


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh", action="store_true", help="Wipe all existing chunks before indexing.")
    args = parser.parse_args()

    print("[1/4] Initializing database...")
    init_db()
    print("      ✓ Done")

    db = SessionLocal()
    try:
        if args.fresh:
            deleted = db.query(KnowledgeChunk).count()
            db.query(KnowledgeChunk).delete()
            db.commit()
            print(f"[2/4] --fresh: deleted {deleted} existing chunks")
        else:
            existing = db.query(KnowledgeChunk).count()
            print(f"[2/4] Chunks already in DB: {existing}  (run with --fresh to wipe and re-index)")

        print("[3/4] Loading documents from knowledge_base/ ...")
        loader = DocumentLoader()
        documents = loader.load_documents()

        if not documents:
            print(f"      ✗ No documents found in: {ROOT / 'knowledge_base'}")
            print("        Supported formats: .md  .pdf  .json")
            return

        for doc in documents:
            print(f"      • {doc['file_name']}  [{doc['source_type']}]")
        print(f"      ✓ {len(documents)} document(s) loaded")

        print("[4/4] Chunking and embedding (may take a minute)...")
        chunker = TextChunker(chunk_size=400, overlap=80)
        indexer = KnowledgeIndexer(db=db)

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

        print(f"      Embedding {len(all_chunks)} chunks...")
        indexed = indexer.index_chunks(all_chunks)

        print(f"\n✅ Done — {indexed} chunks indexed from {len(documents)} document(s)")
        print(f"   Total chunks now in DB: {db.query(KnowledgeChunk).count()}")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
