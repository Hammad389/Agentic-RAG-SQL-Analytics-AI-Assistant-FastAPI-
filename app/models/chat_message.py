from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="active", index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    STATUS_ACTIVE = "active"
    STATUS_CLOSED = "closed"

    def __repr__(self):
        return f"<ChatConversation(id={self.id}, status={self.status})>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id"), index=True)
    sender_type = Column(String, index=True)   # "user" | "assistant" | "system"
    content = Column(String)
    seq = Column(Integer)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, sender_type={self.sender_type})>"
