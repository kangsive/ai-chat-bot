import asyncio
import os
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Response, UploadFile, status, Body
from fastapi.logger import logger
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
import uuid

from app.api import deps
from app.models.chat import Chat, Message, Attachment
from app.models.user import User
from app.schemas.chat import (
    Attachment as AttachmentSchema,
    AttachmentCreate,
    Chat as ChatSchema,
    ChatCreate,
    ChatList,
    ChatUpdate,
    Message as MessageSchema,
    MessageCreate,
    UserMessageRequest,
    StreamingResponse as StreamingResponseSchema
)
from app.services.llm import generate_llm_response
from app.services.file_storage import file_storage_service

router = APIRouter()


@router.get("/", response_model=ChatList)
def get_chats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve all chats for the current user.
    """
    chats = (
        db.query(Chat)
        .filter(Chat.user_id == current_user.id)
        .order_by(Chat.updated_at.desc())  # Order by most recently updated first
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Manually convert each chat to dictionary using model_dump
    chats = [chat.model_dump() for chat in chats]
  
    return {"chats": chats}


@router.post("/", response_model=ChatSchema)
def create_chat(
    *,
    db: Session = Depends(deps.get_db),
    chat_in: ChatCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new chat.
    """
    chat = Chat(
        user_id=current_user.id,
        title=chat_in.title,
        model=chat_in.model,
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat.model_dump()


@router.get("/{chat_id}", response_model=ChatSchema)
def get_chat(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a specific chat by id.
    """
    chat = db.query(Chat).filter(
        Chat.id == chat_id, Chat.user_id == current_user.id
    ).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )
    return chat.model_dump()


@router.put("/{chat_id}", response_model=ChatSchema)
def update_chat(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: uuid.UUID,
    chat_in: ChatUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a chat.
    """
    chat = db.query(Chat).filter(
        Chat.id == chat_id, Chat.user_id == current_user.id
    ).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )
    
    update_data = chat_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chat, field, value)
    
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat.model_dump()


@router.delete("/{chat_id}")
def delete_chat(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a chat.
    """
    chat = db.query(Chat).filter(
        Chat.id == chat_id, Chat.user_id == current_user.id
    ).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )
    
    db.delete(chat)
    db.commit()
    return {"message": "Chat deleted successfully"}


@router.post("/{chat_id}/messages", response_class=StreamingResponse)
async def chat_with_llm(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: uuid.UUID,
    message: str = Form(...),
    files: List[UploadFile] = File(None),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Unified endpoint for sending messages with optional attachments.
    Takes a JSON string in the 'message' form field and optional files.
    
    If editing an existing message (sequence is provided), the backend will:
    1. Keep existing attachments
    2. Add any new uploaded files as additional attachments
    3. Outdated attachments will be deleted by the fronted by calling the delete_attachment endpoint
    
    Returns a streaming response from the LLM.
    """
    # Parse the message JSON
    try:
        message_data = json.loads(message)
        message_obj = UserMessageRequest(**message_data)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid message format: {str(e)}",
        )
    
    # Verify chat exists and belongs to user
    chat = db.query(Chat).filter(
        Chat.id == chat_id, Chat.user_id == current_user.id
    ).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )
    
    # Get the conversation history
    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.sequence)
        .all()
    )
    
    # Check if we're editing an existing message (sequence provided)
    if message_obj.sequence is not None:
        # Find the message with the provided sequence
        existing_message = db.query(Message).filter(
            Message.chat_id == chat_id,
            Message.sequence == message_obj.sequence
        ).first()
        
        if not existing_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message with sequence {message_obj.sequence} not found",
            )
        
        # Verify it's a user message
        if existing_message.role.value != "user":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only user messages can be edited",
            )
        
        # Delete all subsequent messages
        db.query(Message).filter(
            Message.chat_id == chat_id,
            Message.sequence > existing_message.sequence
        ).delete()
        
        # Update the message content
        existing_message.content_json = {"text": message_obj.content}
        existing_message.message_metadata = message_obj.message_metadata
        
        db.add(existing_message)
        db.commit()
        db.refresh(existing_message)
        
        # Handle file attachments - only add new ones
        if files:
            for file in files:
                if file.filename:  # Skip empty file uploads
                    file_data = await file_storage_service.save_file(file, existing_message.id)
                    attachment = Attachment(
                        message_id=existing_message.id,
                        filename=file_data["filename"],
                        file_path=file_data["file_path"],
                        file_type=file_data["file_type"],
                        file_size=file_data["file_size"],
                    )
                    db.add(attachment)
            db.commit()
            db.refresh(existing_message)
        
        # Get the updated conversation history
        messages = (
            db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.sequence)
            .all()
        )
        
        # Format messages for the LLM
        message_history = [msg.to_openai_format() for msg in messages]
        
        # Create assistant message with the next sequence number
        next_sequence = existing_message.sequence + 1
    else:
        # Creating a new message
        # Get the next sequence number
        next_sequence = len(messages) + 1
        
        # Create the user message using the factory method
        user_message = Message.create_user_message(
            chat_id=chat_id,
            content=message_obj.content,
            sequence=next_sequence
        )
        
        # Set additional metadata if provided
        if message_obj.message_metadata:
            user_message.message_metadata = message_obj.message_metadata
            
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # Handle file attachments
        if files:
            for file in files:
                if file.filename:  # Skip empty file uploads
                    file_data = await file_storage_service.save_file(file, user_message.id)
                    attachment = Attachment(
                        message_id=user_message.id,
                        filename=file_data["filename"],
                        file_path=file_data["file_path"],
                        file_type=file_data["file_type"],
                        file_size=file_data["file_size"],
                    )
                    db.add(attachment)
            db.commit()
            db.refresh(user_message)
        
        # Update chat title if it's the first user message
        if next_sequence == 1 and not chat.title:
            title = message_obj.content[:30] + ("..." if len(message_obj.content) > 30 else "")
            chat.title = title
            db.add(chat)
            db.commit()
        
        # Format messages for the LLM including the newly created message
        message_history = [msg.to_openai_format() for msg in messages]
        message_history.append(user_message.to_openai_format())
        
        # Increment for assistant message
        next_sequence += 1
    
    # Generate the assistant response
    async def generate_stream():
        # Create a placeholder for the assistant's response using the factory method
        assistant_message = Message.create_assistant_message(
            chat_id=chat_id,
            content="",  # Will be updated incrementally
            sequence=next_sequence,
            tool_calls=None
        )
        
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        full_response = ""
        
        # Stream the response from the LLM
        async for token in generate_llm_response(message_history):
            full_response += token
            
            # Periodically update the message in the database
            if len(token) > 10:  # Only update every few tokens to reduce DB load
                # Update content_json with new text
                assistant_message.content_json = {"text": full_response}
                db.add(assistant_message)
                db.commit()
                
            # Yield for streaming response
            yield f"data: {token}\n\n"
        
        # Update the final message
        assistant_message.content_json = {"text": full_response}
        db.add(assistant_message)
        db.commit()
        
        yield f"data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
    )


@router.get("/{chat_id}/messages/{message_id}/attachments", response_model=List[AttachmentSchema])
def get_message_attachments(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: uuid.UUID,
    message_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all attachments for a specific message.
    """
    # Verify chat exists and belongs to user
    chat = db.query(Chat).filter(
        Chat.id == chat_id, Chat.user_id == current_user.id
    ).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )
    
    # Verify message exists and belongs to chat
    message = db.query(Message).filter(
        Message.id == message_id, Message.chat_id == chat_id
    ).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    # Get all attachments for the message
    attachments = db.query(Attachment).filter(Attachment.message_id == message_id).all()
    return [attachment.model_dump() for attachment in attachments]


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    *,
    db: Session = Depends(deps.get_db),
    attachment_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Download a specific file attachment.
    """
    # Get the attachment
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found",
        )
    
    # Verify user has access to this attachment
    message = db.query(Message).filter(Message.id == attachment.message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    chat = db.query(Chat).filter(
        Chat.id == message.chat_id, Chat.user_id == current_user.id
    ).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    file_path = attachment.file_path
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server",
        )
    
    # Return the file
    return FileResponse(
        path=file_path, 
        filename=attachment.filename,
        media_type=attachment.file_type
    )


@router.delete("/attachments/{attachment_id}")
def delete_attachment(
    *,
    db: Session = Depends(deps.get_db),
    attachment_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a specific file attachment.
    """
    # Get the attachment
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found",
        )
    
    # Verify user has access to this attachment
    message = db.query(Message).filter(Message.id == attachment.message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    chat = db.query(Chat).filter(
        Chat.id == message.chat_id, Chat.user_id == current_user.id
    ).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Delete the file from storage
    file_storage_service.delete_file(attachment.file_path)
    
    # Delete the database record
    db.delete(attachment)
    db.commit()
    
    return {"message": "Attachment deleted successfully"}


@router.delete("/{chat_id}/messages/{message_id}/attachments/{attachment_id}")
async def delete_message_attachment(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: uuid.UUID,
    message_id: uuid.UUID,
    attachment_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a specific attachment from a message.
    This endpoint allows the frontend to directly manage attachments.
    """
    # Verify chat exists and belongs to user
    chat = db.query(Chat).filter(
        Chat.id == chat_id, Chat.user_id == current_user.id
    ).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )
    
    # Verify message exists and belongs to chat
    message = db.query(Message).filter(
        Message.id == message_id, Message.chat_id == chat_id
    ).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    # Verify it's a user message
    if message.role.value != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only attachments from user messages can be deleted",
        )
    
    # Find and delete the attachment
    attachment = db.query(Attachment).filter(
        Attachment.id == attachment_id, 
        Attachment.message_id == message_id
    ).first()
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found",
        )
    
    # Delete the file from storage
    file_storage_service.delete_file(attachment.file_path)
    
    # Delete the database record
    db.delete(attachment)
    db.commit()
    
    return {"message": "Attachment deleted successfully"} 