from abc import ABC, abstractmethod
from typing import List, Tuple

from app.domain.entities import ChatMessageEntity


class ChatRepository(ABC):
    @abstractmethod
    def get_or_create_active_conversation(self) -> object:
        pass

    @abstractmethod
    def get_last_seq(self, conversation_id: int) -> int:
        pass

    @abstractmethod
    def get_recent_messages_for_context(self, conversation_id: int, limit: int) -> List[str]:
        pass

    @abstractmethod
    def save_message(self, entity: ChatMessageEntity) -> ChatMessageEntity:
        pass

    @abstractmethod
    def list_recent_messages(self, conversation_id: int, limit: int) -> List[Tuple[str, str]]:
        pass
