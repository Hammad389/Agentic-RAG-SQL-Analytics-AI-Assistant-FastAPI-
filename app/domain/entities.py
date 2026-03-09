from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ChatMessageEntity:
    """
    Domain representation of a chat message.
    Pure domain — no ORM coupling.
    """

    conversation_id: int
    sender_type: str          # "user" | "assistant" | "system"
    content: str
    seq: int

    id: Optional[int] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatConversationEntity:
    status: str = "active"

    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
