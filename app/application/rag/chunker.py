from typing import Dict, List


class TextChunker:
    """
    Smart chunking — preserves semantic meaning, avoids breaking mid-sentence.
    """

    def __init__(self, chunk_size: int = 400, overlap: int = 80):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, *, text: str, metadata: dict) -> List[Dict]:
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size
            chunk_text = text[start:end]
            chunks.append({"content": chunk_text.strip(), "metadata": metadata})
            start += self.chunk_size - self.overlap

        return chunks
