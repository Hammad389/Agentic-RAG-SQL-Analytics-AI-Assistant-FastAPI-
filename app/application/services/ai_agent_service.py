from typing import Optional

from sqlalchemy.orm import Session

from app.application.agent.graph.agent_graph import AgenticRagGraph
from app.application.agent.state import AgentState
from app.domain.entities import ChatMessageEntity
from app.domain.enums import SenderType
from app.domain.services.chat_repository import ChatRepository


class ChatService:
    """
    Orchestrates a single chat turn.

    repo is optional — when None (no-user / testing mode),
    conversation persistence is skipped entirely.
    """

    def __init__(self, db: Session, repo: Optional[ChatRepository] = None):
        self.repo = repo
        # Graph is instantiated per-request so it gets the correct db session
        self.graph = AgenticRagGraph(db=db)

    def _extract_message_text(self, response_obj) -> str:
        if response_obj is None:
            return ""
        if isinstance(response_obj, str):
            return response_obj
        if isinstance(response_obj, dict):
            data = response_obj.get("data")
            if isinstance(data, dict):
                return str(data.get("message", ""))
            return str(data) if data else ""
        return str(response_obj)

    def ai_agent_handler(self, *, message: str, user_id: Optional[int] = None) -> dict:
        conversation = None
        last_seq = 0

        # Persist user message only when repo + conversation tracking is available
        if self.repo is not None and user_id is not None:
            conversation = self.repo.get_or_create_active_conversation()
            last_seq = self.repo.get_last_seq(conversation.id)
            self.repo.save_message(
                ChatMessageEntity(
                    conversation_id=conversation.id,
                    sender_type=SenderType.USER.value,
                    content=message,
                    seq=last_seq + 1,
                )
            )

        state = AgentState(message=message, user_id=user_id)
        result_state = self.graph.run(state)

        # Persist assistant reply
        if self.repo is not None and conversation is not None:
            content = self._extract_message_text(result_state.response)
            self.repo.save_message(
                ChatMessageEntity(
                    conversation_id=conversation.id,
                    sender_type=SenderType.ASSISTANT.value,
                    content=content,
                    seq=last_seq + 2,
                    metadata={
                        "intent": result_state.intents,
                        "execution_plan": result_state.execution_plan,
                        "usage": result_state.usage,
                    },
                )
            )

        return result_state.response
