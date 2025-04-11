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
from app.models.chat import Chat, Message, Attachment, MessageRole
from app.models.user import User
from app.crud.chat import chat
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
    chats = chat.get_user_chats(db, user_id=current_user.id, skip=skip, limit=limit)

    # Manually convert each chat to dictionary using model_dump
    chats = [c.model_dump() for c in chats]
  
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
    new_chat = chat.create(db, obj_in=chat_in, user_id=current_user.id)
    return new_chat.model_dump()


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
    chat_obj = chat.get(db, chat_id=chat_id, user_id=current_user.id)
    if not chat_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )
    return chat_obj.model_dump()


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
    chat_obj = chat.get(db, chat_id=chat_id, user_id=current_user.id)
    if not chat_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )
    
    updated_chat = chat.update(db, db_obj=chat_obj, obj_in=chat_in)
    return updated_chat.model_dump()


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
    success = chat.delete(db, chat_id=chat_id, user_id=current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )
    
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
        logger.info(f"Message object: {message_obj}")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid message format: {str(e)}",
        )
    
    # Verify chat exists and belongs to user
    chat_obj = chat.get(db, chat_id=chat_id, user_id=current_user.id)
    if not chat_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )
    
    # Get the conversation history
    messages = chat.get_messages(db, chat_id=chat_id)
    
    # Check if we're editing an existing message (sequence provided)
    if message_obj.sequence is not None:
        # Find the message with the provided sequence
        existing_message = chat.get_message_by_sequence(db, sequence=message_obj.sequence, chat_id=chat_id)
        
        if not existing_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message with sequence {message_obj.sequence} not found",
            )
        
        # Verify it's a user message
        if existing_message.role != MessageRole.USER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only user messages can be edited",
            )
        
        # Delete all subsequent messages
        deleted = chat.delete_messages_after_sequence(db, chat_id=chat_id, sequence=existing_message.sequence)
        logger.info(f"Deleted {deleted} messages after sequence {existing_message.sequence} of chat {chat_id}")
        
        # Update the message content
        chat.update_message(
            db, 
            db_obj=existing_message, 
            content={"content": [{"type": "text", "text": message_obj.content}]},
            message_metadata=message_obj.message_metadata
        )
        
        # Handle file attachments - only add new ones
        if files:
            for file in files:
                if file.filename:  # Skip empty file uploads
                    file_data = await file_storage_service.save_file(file, existing_message.id)
                    chat.create_attachment(
                        db,
                        message_id=existing_message.id,
                        filename=file_data["filename"],
                        file_path=file_data["file_path"],
                        file_type=file_data["file_type"],
                        file_size=file_data["file_size"],
                    )
        
        # Use the existing message
        user_message = existing_message
    else:
        # This is a new message, create it
        
        # Get the next sequence number
        next_sequence = len(messages) + 1
        
        # Create the user message
        user_message = chat.create_message(
            db,
            obj_in=MessageCreate(
                role=MessageRole.USER,
                content=[{"type": "text", "text": message_obj.content}],
                sequence=next_sequence,
                message_metadata=message_obj.message_metadata
            ),
            chat_id=chat_id
        )
        
        # Handle file attachments
        if files:
            for file in files:
                if file.filename:  # Skip empty file uploads
                    file_data = await file_storage_service.save_file(file, user_message.id)
                    chat.create_attachment(
                        db,
                        message_id=user_message.id,
                        filename=file_data["filename"],
                        file_path=file_data["file_path"],
                        file_type=file_data["file_type"],
                        file_size=file_data["file_size"],
                    )
    
    # Update the chat's updated_at timestamp
    chat.update(db, db_obj=chat_obj, obj_in={"title": chat_obj.title})
    
    # Prepare for assistant's response (next sequence)
    assistant_sequence = user_message.sequence + 1
    
    # Get updated conversation history
    updated_messages = chat.get_messages(db, chat_id=chat_id)
    
    # Format db messages to openai messages
    formatted_messages = [msg.to_openai_format() for msg in updated_messages]
    
    # Create a function to generate and stream the response
    async def generate_stream():
        # Create a placeholder for the assistant's response using the CRUD function
        assistant_message = chat.create_message(
            db,
            obj_in=MessageCreate(
                role=MessageRole.ASSISTANT,
                content=[{"type": "text", "text": ""}],
                sequence=assistant_sequence
            ),
            chat_id=chat_id
        )
        
        content_so_far = ""
        
        # Pass the formatted messages and model to the LLM service
        async for token in generate_llm_response(formatted_messages, chat_obj.model):
            content_so_far += token
            
            # Update the message content in the database periodically using the CRUD function
            chat.update_assistant_message(
                db, 
                message_id=assistant_message.id, 
                content=content_so_far
            )
            
            # Stream the token to the client
            yield f"data: {token}\n\n"
        
        # Final update to mark completion using the CRUD function
        chat.update_assistant_message(
            db, 
            message_id=assistant_message.id, 
            content=content_so_far,
            is_complete=True
        )
        
        # Send completion signal
        yield f"data: [DONE]\n\n"
    
    # Return the streaming response with the correct media type
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
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
    chat_obj = chat.get(db, chat_id=chat_id, user_id=current_user.id)
    if not chat_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )
    
    # Verify message exists and belongs to the chat
    message = chat.get_message(db, message_id=message_id, chat_id=chat_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    # Get attachments
    attachments = chat.get_attachments(db, message_id=message_id)
    return attachments


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    *,
    db: Session = Depends(deps.get_db),
    attachment_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Download an attachment.
    """
    # Get the attachment
    attachment = chat.get_attachment(db, attachment_id=attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found",
        )
    
    # Verify the user has access to this attachment
    # This is done by checking if the message's chat belongs to the user
    message = db.query(Message).filter(Message.id == attachment.message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    chat_obj = chat.get(db, chat_id=message.chat_id, user_id=current_user.id)
    if not chat_obj:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this attachment",
        )
    
    # Check if the file exists
    if not file_storage_service.is_file_exists(attachment.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    # Return the file
    return FileResponse(
        path=attachment.file_path,
        filename=attachment.filename,
        media_type=attachment.file_type,
    )


@router.delete("/attachments/{attachment_id}")
def delete_attachment(
    *,
    db: Session = Depends(deps.get_db),
    attachment_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an attachment.
    """
    # Get the attachment
    attachment = chat.get_attachment(db, attachment_id=attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found",
        )
    
    # Verify the user has access to this attachment
    # This is done by checking if the message's chat belongs to the user
    message = db.query(Message).filter(Message.id == attachment.message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    chat_obj = chat.get(db, chat_id=message.chat_id, user_id=current_user.id)
    if not chat_obj:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this attachment",
        )
    
    # Delete the file from storage
    file_storage_service.delete_file(attachment.file_path)
    
    # Delete the attachment from the database
    success = chat.delete_attachment(db, attachment_id=attachment_id)
    
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
    chat_obj = chat.get(db, chat_id=chat_id, user_id=current_user.id)
    if not chat_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )
    
    # Verify message exists and belongs to the chat
    message = chat.get_message(db, message_id=message_id, chat_id=chat_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    # Get the attachment
    attachment = chat.get_attachment(db, attachment_id=attachment_id)
    if not attachment or attachment.message_id != message_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found",
        )
    
    # Delete the database record
    success = chat.delete_attachment(db, attachment_id=attachment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found",
        )
    
    # Delete the file from storage
    file_storage_service.delete_file(attachment.file_path)
    
    return {"message": "Attachment deleted successfully"} 