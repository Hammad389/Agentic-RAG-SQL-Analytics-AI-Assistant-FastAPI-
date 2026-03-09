from typing import List, Tuple

from sqlalchemy.orm import Session

from app.domain.entities import ChatMessageEntity
from app.domain.services.chat_repository import ChatRepository
from app.models.chat_message import ChatConversation, ChatMessage


class FastAPIChatRepository(ChatRepository):
    """
    SQLAlchemy implementation of ChatRepository for FastAPI.
    Replaces the old DjangoChatRepository.
    Each method receives or uses the injected db session.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_active_conversation(self) -> ChatConversation:
        convo = (
            self.db.query(ChatConversation)
            .filter(ChatConversation.status == ChatConversation.STATUS_ACTIVE)
            .order_by(ChatConversation.created_at.desc())
            .first()
        )

        if not convo:
            convo = ChatConversation(status=ChatConversation.STATUS_ACTIVE)
            self.db.add(convo)
            self.db.commit()
            self.db.refresh(convo)

        return convo

    def get_last_seq(self, conversation_id: int) -> int:
        last = (
            self.db.query(ChatMessage.seq)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.seq.desc())
            .scalar()
        )
        return int(last or 0)

    def get_recent_messages_for_context(self, conversation_id: int, limit: int = 5) -> List[str]:
        """
        Fetch recent messages from the conversation to build context.
        Returns messages in chronological order.
        """
        messages = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )
        # Reverse to get chronological order
        return [m.content for m in reversed(messages)]

    def save_message(self, entity: ChatMessageEntity) -> ChatMessageEntity:
        msg = ChatMessage(
            conversation_id=entity.conversation_id,
            sender_type=entity.sender_type,
            content=entity.content,
            seq=entity.seq,
            metadata_=entity.metadata or {},
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)

        entity.id = msg.id
        entity.created_at = msg.created_at
        return entity

    def list_recent_messages(self, conversation_id: int, limit: int) -> List[Tuple[str, str]]:
        rows = (
            self.db.query(ChatMessage.sender_type, ChatMessage.content)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.seq.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(rows))
