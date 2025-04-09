import uuid
import base64
import os
import enum
from typing import List, Optional, Union, Dict, Any, Literal

from fastapi.logger import logger
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates
from pydantic import BaseModel

from app.models.base import Base


# File type constants
class FileType(enum.Enum):
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"
    OTHER = "other"

# Content type map by MIME type
MIME_TYPE_MAP = {
    'image/jpeg': FileType.IMAGE,
    'image/png': FileType.IMAGE,
    'image/gif': FileType.IMAGE, 
    'image/webp': FileType.IMAGE,
    'audio/mpeg': FileType.AUDIO,
    'audio/mp4': FileType.AUDIO,
    'audio/wav': FileType.AUDIO,
    'audio/webm': FileType.AUDIO,
    'application/pdf': FileType.DOCUMENT,
    'application/msword': FileType.DOCUMENT,
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': FileType.DOCUMENT,
}

# Message role enum
class MessageRole(enum.Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

# Content type for structured content
class ContentType(enum.Enum):
    TEXT = "text"
    IMAGE_URL = "image_url"
    INPUT_AUDIO = "input_audio"

# Pydantic models for validation
class TextContent(BaseModel):
    type: Literal["text"]
    text: str

class ImageUrlContent(BaseModel):
    type: Literal["image_url"]
    image_url: Dict[str, str]

class AudioContent(BaseModel):
    type: Literal["input_audio"]
    input_audio: Dict[str, str]

ContentItem = Union[TextContent, ImageUrlContent, AudioContent]

class ToolFunction(BaseModel):
    name: str
    arguments: Optional[str] = None

class ToolCall(BaseModel):
    id: str
    type: str
    function: Optional[ToolFunction] = None

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
    
    def model_dump(self):
        """Convert the model to a dictionary compatible with Pydantic schemas."""
        return {
            "id": self.id,
            "title": self.title,
            "user_id": self.user_id,
            "model": self.model,
            "is_archived": self.is_archived,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [message.model_dump() for message in self.messages] if self.messages else []
        }


# Base Message class
class Message(Base):
    """Base class for all message types in a chat conversation."""
    
    __tablename__ = "message"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chat.id"), nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    sequence = Column(Integer, nullable=False)  # Message order in the conversation
    
    # Common content field (JSON for all types)
    content_json = Column(JSONB, nullable=True)
    
    # Metadata fields
    tokens = Column(Integer, nullable=True)
    message_metadata = Column(JSONB, nullable=True)
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")
    attachments = relationship("Attachment", back_populates="message", cascade="all, delete-orphan")
    
    # Add model_dump method for Pydantic schema compatibility, this is important when queried data
    #  need to be validated by Pydantic schemas
    def model_dump(self):
        """Convert the model to a dictionary compatible with Pydantic schemas."""
        # Handle different message roles and content types
        if self.role == MessageRole.TOOL:
            if self.text_content:
                content = self.text_content
            else:
                structured_content = self.structured_content
                flattened_content = "\n".join([item.get("text", "") for item in structured_content if item.get("type") == "text"])
                content = flattened_content
        elif self.role == MessageRole.USER:
            if self.text_content:
                content = self.text_content
            elif self.structured_content:
                # Extract text content from structured content for user messages
                text_items = [item.get("text", "") for item in self.structured_content if item.get("type") == "text"]
                image_items = [f"[Image: {idx+1}]" for idx, item in enumerate(self.structured_content) if item.get("type") == "image_url"]
                audio_items = [f"[Audio: {idx+1}]" for idx, item in enumerate(self.structured_content) if item.get("type") == "input_audio"]
                
                # Combine all content types
                all_items = text_items + image_items + audio_items
                content = "\n".join(all_items)
            else:
                content = ""
        else:
            content = self.text_content

        content = self.text_content
        
        # Ensure content is never None to match Pydantic schema
        if content is None:
            content = ""
        
        result = {
            "id": self.id,
            "chat_id": self.chat_id,
            "role": self.role.value,  # Convert Enum to string value
            "sequence": self.sequence,
            "content": content,  # Required string field in Pydantic schema
            "reasoning_content": None,
            "tokens": self.tokens,
            "message_metadata": self.message_metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "attachments": [attachment.model_dump() for attachment in self.attachments] if self.attachments else []
        }
        return result
    
    # Factory methods for different message types
    @classmethod
    def create_system_message(cls, chat_id: uuid.UUID, content: str, sequence: int) -> "Message":
        """Create a system message with text content."""
        return cls(
            chat_id=chat_id,
            role=MessageRole.SYSTEM,
            sequence=sequence,
            content_json={"text": content}
        )
    
    @classmethod
    def create_user_message(cls, chat_id: uuid.UUID, content: Union[str, List[Dict[str, Any]]], sequence: int) -> "Message":
        """Create a user message with text or structured content."""
        if isinstance(content, str):
            content_json = {"text": content}
        else:
            # Validate structured content
            for item in content:
                if "type" not in item:
                    raise ValueError("Each content item must have a 'type' field")
                if item["type"] not in [t.value for t in ContentType]:
                    raise ValueError(f"Invalid content type: {item['type']}")
            content_json = {"structured": content}
        
        return cls(
            chat_id=chat_id,
            role=MessageRole.USER,
            sequence=sequence,
            content_json=content_json
        )
    
    @classmethod
    def create_assistant_message(cls, chat_id: uuid.UUID, content: Optional[str], sequence: int, 
                                tool_calls: Optional[List[Dict[str, Any]]] = None) -> "Message":
        """Create an assistant message with optional tool calls."""
        content_json = {"text": content}
        
        if tool_calls:
            # Validate tool calls using Pydantic model
            validated_tool_calls = []
            for call_data in tool_calls:
                # Convert to ToolCall model to validate
                tool_call = ToolCall(**call_data)
                validated_tool_calls.append(tool_call.model_dump())
            content_json["tool_calls"] = validated_tool_calls
        
        return cls(
            chat_id=chat_id,
            role=MessageRole.ASSISTANT,
            sequence=sequence,
            content_json=content_json
        )
    
    @classmethod
    def create_tool_message(cls, chat_id: uuid.UUID, content: Union[str, List[Dict[str, Any]]], tool_call_id: str, sequence: int) -> "Message":
        """Create a tool message with text content and tool_call_id."""
        if not tool_call_id:
            raise ValueError("Tool message must have a tool_call_id")
        
        content_json = {"tool_call_id": tool_call_id}
        
        if isinstance(content, str):
            content_json["text"] = content
        else:
            # Validate structured content, tool message support only text (not image or audio)
            for item in content:
                if "type" not in item:
                    raise ValueError("Each content item must have a 'type' field")
                if item["type"] != ContentType.TEXT.value:
                    raise ValueError(f"Invalid content type for tool message: {item['type']}")
            content_json["structured"] = content
        
        return cls(
            chat_id=chat_id,
            role=MessageRole.TOOL,
            sequence=sequence,
            content_json=content_json
        )
    
    @classmethod
    def from_openai_format(cls, message_data: Dict[str, Any], chat_id: uuid.UUID, sequence: int) -> "Message":
        """Create a Message instance from OpenAI API format."""
        role = MessageRole(message_data["role"])
        content = message_data.get("content")
        
        if role == MessageRole.SYSTEM:
            return cls.create_system_message(chat_id, content, sequence)
        elif role == MessageRole.USER:
            return cls.create_user_message(chat_id, content, sequence)
        elif role == MessageRole.ASSISTANT:
            return cls.create_assistant_message(
                chat_id, 
                content, 
                sequence,
                message_data.get("tool_calls")
            )
        elif role == MessageRole.TOOL:
            return cls.create_tool_message(
                chat_id,
                content,
                message_data.get("tool_call_id"),
                sequence
            )
        else:
            raise ValueError(f"Unsupported message role: {role}")
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert the message to OpenAI API compatible format."""
        result = {"role": self.role.value}
        
        if self.role == MessageRole.SYSTEM:
            result["content"] = self.content_json.get("text", "")
        
        elif self.role == MessageRole.USER:
            if "structured" in self.content_json:
                # Handle structured content with attachments
                structured_content = self.content_json["structured"]
                
                # Process any attachments
                if self.attachments:
                    content_list = self._process_attachments(structured_content)
                    result["content"] = content_list
                else:
                    result["content"] = structured_content
            else:
                # Simple text content
                text_content = self.content_json.get("text", "")
                
                # Process any attachments
                if self.attachments:
                    content_list = self._process_attachments([{"type": "text", "text": text_content}])
                    result["content"] = content_list
                else:
                    result["content"] = text_content
        
        elif self.role == MessageRole.ASSISTANT:
            result["content"] = self.content_json.get("text", "")
            
            # Add tool_calls if present
            if "tool_calls" in self.content_json:
                result["tool_calls"] = self.content_json["tool_calls"]
        
        elif self.role == MessageRole.TOOL:
            if "structured" in self.content_json:
                result["content"] = self.content_json.get("structured", [])
            else:
                result["content"] = self.content_json.get("text", "")
            result["tool_call_id"] = self.content_json.get("tool_call_id")
        
        return result
    
    def _process_attachments(self, base_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process attachments and add them to content list."""
        content_list = list(base_content) if base_content else []
        
        for attachment in self.attachments:
            file_type = MIME_TYPE_MAP.get(attachment.file_type, FileType.OTHER)
            
            if file_type == FileType.IMAGE:
                # Convert image to base64
                try:
                    with open(attachment.file_path, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                        content_list.append({
                            'type': 'image_url',
                            'image_url': {
                                'url': f"data:{attachment.file_type};base64,{base64_image}"
                            }
                        })
                except Exception as e:
                    content_list.append({
                        'type': 'text',
                        'text': f"[Image: {attachment.filename} (could not be loaded: {str(e)})]"
                    })
            
            elif file_type == FileType.AUDIO:
                # Handle audio
                try:
                    with open(attachment.file_path, "rb") as audio_file:
                        base64_audio = base64.b64encode(audio_file.read()).decode('utf-8')
                        content_list.append({
                            'type': 'text',
                            'text': f"[Audio data in base64: {base64_audio[:20]}...]"
                        })
                except Exception as e:
                    content_list.append({
                        'type': 'text',
                        'text': f"[Audio: {attachment.filename} (could not be loaded: {str(e)})]"
                    })
            
            else:
                # For other file types
                file_size_mb = attachment.file_size / (1024 * 1024) if attachment.file_size else "unknown"
                content_list.append({
                    'type': 'text',
                    'text': f"[File: {attachment.filename}, Type: {attachment.file_type}, Size: {file_size_mb:.2f}MB]"
                })
        
        return content_list
    
    # Properties for easier access to content
    @property
    def text_content(self) -> Optional[str]:
        """Get text content if available."""
        if not self.content_json:
            return None
        return self.content_json.get("text")
    
    @property
    def structured_content(self) -> Optional[List[Dict[str, Any]]]:
        """Get structured content if available."""
        if not self.content_json:
            return None
        return self.content_json.get("structured")
    
    @property
    def tool_calls(self) -> Optional[List[Dict[str, Any]]]:
        """Get tool calls if available."""
        if not self.content_json:
            return None
        return self.content_json.get("tool_calls")
    
    @property
    def tool_call_id(self) -> Optional[str]:
        """Get tool call ID if available."""
        if not self.content_json:
            return None
        return self.content_json.get("tool_call_id")
    
    @validates('content_json')
    def validate_content(self, key, value):
        """Validate content format based on role."""
        if not value:
            return value
            
        # Validate by role
        if self.role == MessageRole.SYSTEM:
            if "text" not in value:
                raise ValueError("System message must have text content")
                
        elif self.role == MessageRole.USER:
            if "text" not in value and "structured" not in value:
                raise ValueError("User message must have either text or structured content")
            
            # Validate structured content if present
            if "structured" in value:
                structured = value["structured"]
                if not isinstance(structured, list):
                    raise ValueError("Structured content must be a list")
                for item in structured:
                    try:
                        content_type = item.get("type")
                        if content_type == "text":
                            TextContent(**item)
                        elif content_type == "image_url":
                            ImageUrlContent(**item)
                        elif content_type == "input_audio":
                            AudioContent(**item)
                        else:
                            raise ValueError(f"Unknown content type: {content_type}")
                    except Exception as e:
                        raise ValueError(f"Invalid content item: {str(e)}")
        
        elif self.role == MessageRole.ASSISTANT:
            if "text" not in value:
                raise ValueError("Assistant message must have text content")
            
            # Validate tool_calls if present
            if "tool_calls" in value:
                try:
                    tool_calls = value["tool_calls"]
                    if not isinstance(tool_calls, list):
                        raise ValueError("tool_calls must be a list")
                    
                    for call_data in tool_calls:
                        ToolCall(**call_data)
                except Exception as e:
                    raise ValueError(f"Invalid tool calls: {str(e)}")
        
        elif self.role == MessageRole.TOOL:
            # Tool messages must have tool_call_id and either text or structured content
            if "tool_call_id" not in value:
                raise ValueError("Tool message must have tool_call_id")
                
            if "text" not in value and "structured" not in value:
                raise ValueError("Tool message must have either text or structured content")
                
            # Validate structured content if present
            if "structured" in value:
                structured = value["structured"]
                if not isinstance(structured, list):
                    raise ValueError("Structured content must be a list")
                for item in structured:
                    try:
                        content_type = item.get("type")
                        if content_type != "text":
                            raise ValueError(f"Tool message only supports text content type, got: {content_type}")
                        TextContent(**item)
                    except Exception as e:
                        raise ValueError(f"Invalid content item: {str(e)}")
                
        return value


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
    
    @property
    def file_category(self) -> FileType:
        """Get the file category based on MIME type."""
        return MIME_TYPE_MAP.get(self.file_type, FileType.OTHER)
        
    def model_dump(self):
        """Convert the model to a dictionary compatible with Pydantic schemas."""
        return {
            "id": self.id,
            "message_id": self.message_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "attachment_metadata": self.attachment_metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }