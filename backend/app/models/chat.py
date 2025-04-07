import uuid
from typing import List, Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class Chat(Base):
    """Model representing a conversation session."""
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    model = Column(String(100), nullable=True)  # The LLM model used
    is_archived = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan", order_by="Message.sequence")


class Message(Base):
    """Individual message in a chat conversation."""
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chat.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'tool'
    content = Column(Text, nullable=False)
    reasoning_content = Column(Text, nullable=True)  # Optional reasoning content
    sequence = Column(Integer, nullable=False)  # Message order in the conversation
    
    # Optional fields for metadata
    tokens = Column(Integer, nullable=True)  # Token count
    message_metadata = Column(JSONB, nullable=True)  # Any additional message-specific metadata
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")
    attachments = relationship("Attachment", back_populates="message", cascade="all, delete-orphan")
    
    # Add check constraint for role
    __table_args__ = (
        CheckConstraint(role.in_(["system", "user", "assistant", "tool"]), name="check_message_role"),
    )


class Attachment(Base):
    """Model for storing file attachment metadata linked to messages."""
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("message.id"), nullable=False)
    
    # File metadata
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)  # Path or URL to the actual file storage
    file_type = Column(String(100), nullable=False)  # MIME type or file extension
    file_size = Column(Integer, nullable=True)  # Size in bytes
    
    # Additional metadata for the attachment
    attachment_metadata = Column(JSONB, nullable=True)
    
    # Relationships
    message = relationship("Message", back_populates="attachments") 