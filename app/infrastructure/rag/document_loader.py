import json
import os
from pathlib import Path
from typing import Dict, List

import fitz  # PyMuPDF

# Resolve relative to this file so it works regardless of cwd
_HERE = Path(__file__).resolve().parent
KNOWLEDGE_PATH = Path(os.getenv("KNOWLEDGE_BASE_PATH", str(_HERE.parent.parent.parent / "knowledge_base")))


class DocumentLoader:
    """
    Loads ALL supported knowledge files.

    Supports:
    - Markdown (.md)
    - PDF (.pdf)
    - JSON (.json)
    """

    SUPPORTED_EXTENSIONS = {".md", ".pdf", ".json"}

    def load_documents(self) -> List[Dict]:
        documents = []

        if not KNOWLEDGE_PATH.exists():
            print(f"[DocumentLoader] WARNING: knowledge_base path not found: {KNOWLEDGE_PATH}")
            return documents

        for file in KNOWLEDGE_PATH.iterdir():
            if file.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue
            if file.suffix.lower() == ".md":
                documents.append(self._load_markdown(file))
            elif file.suffix.lower() == ".pdf":
                documents.append(self._load_pdf(file))
            elif file.suffix.lower() == ".json":
                documents.extend(self._load_json(file))

        return documents

    def _load_markdown(self, file: Path) -> Dict:
        return {
            "title": file.stem,
            "content": file.read_text(encoding="utf-8"),
            "source_type": "platform",
            "file_name": file.name,
        }

    def _load_pdf(self, file: Path) -> Dict:
        text = ""
        with fitz.open(file) as doc:
            for page in doc:
                text += page.get_text()
        return {
            "title": file.stem,
            "content": text,
            "source_type": "policy",
            "file_name": file.name,
        }

    def _load_json(self, file: Path) -> List[Dict]:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents = []
        description = data.get("description", "")
        intents = data.get("intents", [])

        for intent in intents:
            intent_id = intent.get("id", "")
            intent_type = intent.get("type", "")
            label = intent.get("label", "")
            url = intent.get("url", "")
            examples = intent.get("examples", [])
            notes = intent.get("notes", "")

            content = f"""
                Global Description:
                {description}

                Intent ID: {intent_id}
                Type: {intent_type}
                Label: {label}
                URL: {url}

                User Example Queries:
                {chr(10).join(examples)}

                Notes:
                {notes}

                If a user query is semantically similar to the examples,
                the correct navigation URL is: {url}
                """.strip()

            documents.append(
                {
                    "title": f"{file.stem}::{intent_id}",
                    "content": content,
                    "source_type": "intent_navigation",
                    "file_name": file.name,
                }
            )

        return documents
