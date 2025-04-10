from datetime import datetime
import uuid
from typing import Any, Dict, List, Optional, Literal, Union

from pydantic import BaseModel, Field, UUID4, ConfigDict


# Attachment schemas
class AttachmentBase(BaseModel):
    filename: str = Field(..., description="Original filename of the attachment")
    file_path: str = Field(..., description="Path or URL to the file storage")
    file_type: str = Field(..., description="MIME type or file extension")
    file_size: Optional[int] = Field(None, description="Size of the file in bytes")
    attachment_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the attachment")


class AttachmentCreate(AttachmentBase):
    pass


class AttachmentInDBBase(AttachmentBase):
    id: UUID4
    message_id: UUID4
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Attachment(AttachmentInDBBase):
    pass


# Message schemas
class MessageBase(BaseModel):
    role: Literal["system", "user", "assistant", "tool"] = Field(..., description="The role of the message sender (system, user, assistant, tool)")
    content: Union[str, List[Dict[str, Any]]] = Field(..., description="The content of the message (text or structured data)")
    reasoning_content: Optional[str] = Field(None, description="Optional reasoning content for the message")
    sequence: int = Field(..., description="The sequence number of the message in the chat")
    tokens: Optional[int] = Field(None, description="The token count of the message")
    message_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the message")


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    tokens: Optional[int] = None
    message_metadata: Optional[Dict[str, Any]] = None


class MessageResendUpdate(BaseModel):
    new_content: str = Field(..., description="The new content for the message to be updated")


class UserMessageRequest(BaseModel):
    role: Literal["user"] = Field("user", description="The role of the message sender (only user supported)")
    content: Union[str, List[Dict[str, Any]]] = Field(..., description="The content of the message (text or structured data)")
    sequence: Optional[int] = Field(None, description="Sequence number for editing existing messages")
    reasoning_content: Optional[str] = Field(None, description="Optional reasoning content")
    message_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the message")
    # attachments will be handled via form data


class MessageInDBBase(MessageBase):
    id: UUID4
    chat_id: UUID4
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Message(MessageInDBBase):
    attachments: List[Attachment] = []


# Chat schemas
class ChatBase(BaseModel):
    title: Optional[str] = Field(None, description="The title of the chat")
    model: Optional[str] = Field(None, description="The LLM model used for this chat")
    is_archived: Optional[bool] = Field(False, description="Whether the chat is archived")


class ChatCreate(ChatBase):
    pass


class ChatUpdate(ChatBase):
    pass


class ChatInDBBase(ChatBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Chat(ChatInDBBase):
    messages: List[Message] = []


class ChatList(BaseModel):
    chats: List[Chat] = []


# For streaming responses
class StreamingResponse(BaseModel):
    text: str
    done: bool = False 