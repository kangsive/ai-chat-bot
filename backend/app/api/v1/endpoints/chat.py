import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import uuid

from app.api import deps
from app.models.chat import Chat, Message
from app.models.user import User
from app.schemas.chat import (
    Chat as ChatSchema,
    ChatCreate,
    ChatList,
    ChatUpdate,
    Message as MessageSchema,
    MessageCreate,
    MessageResendUpdate,
    StreamingResponse as StreamingResponseSchema
)
from app.services.llm import generate_llm_response

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
    return chat


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
    return chat


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
    return chat


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


@router.post("/{chat_id}/messages", response_model=MessageSchema)
def create_message(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: uuid.UUID,
    message_in: MessageCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new message in a chat.
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
    
    # Get the next sequence number
    last_message = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.sequence.desc())
        .first()
    )
    sequence = (last_message.sequence + 1) if last_message else 1
    
    # Create the message
    message = Message(
        chat_id=chat_id,
        role=message_in.role,
        content=message_in.content,
        reasoning_content=message_in.reasoning_content,
        sequence=sequence,
        tokens=message_in.tokens,
        message_metadata=message_in.message_metadata,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Update chat title if it's the first user message and no title yet
    if sequence == 1 and message.role == "user" and not chat.title:
        # Create a title from the first few words
        title = message.content[:30] + ("..." if len(message.content) > 30 else "")
        chat.title = title
        db.add(chat)
        db.commit()
    
    return message


@router.post("/{chat_id}/chat", response_class=StreamingResponse)
async def chat_with_llm(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: uuid.UUID,
    message_content: str,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Send a message to the LLM and get a streaming response.
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
    
    # Get the conversation history
    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.sequence)
        .all()
    )
    
    # Format messages for the LLM
    message_history = [{"role": msg.role, "content": msg.content} for msg in messages]
    
    # Get the next sequence number
    next_sequence = len(messages) + 1
    
    # Create the user message
    user_message = Message(
        chat_id=chat_id,
        role="user",
        content=message_content,
        sequence=next_sequence,
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Update chat title if it's the first user message and no title yet
    if next_sequence == 1 and not chat.title:
        # Create a title from the first few words
        title = message_content[:30] + ("..." if len(message_content) > 30 else "")
        chat.title = title
        db.add(chat)
        db.commit()
    
    # Add the new message to history
    message_history.append({"role": "user", "content": message_content})
    
    # Generate the assistant response
    async def generate_stream():
        # Create a placeholder for the assistant's response
        assistant_message = Message(
            chat_id=chat_id,
            role="assistant",
            content="",  # Will be updated incrementally
            sequence=next_sequence + 1,
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
                assistant_message.content = full_response
                db.add(assistant_message)
                db.commit()
                
            # Yield for streaming response
            yield f"data: {token}\n\n"
        
        # Update the final message
        assistant_message.content = full_response
        db.add(assistant_message)
        db.commit()
        
        yield f"data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
    )


@router.put("/{chat_id}/messages/{message_id}", response_class=StreamingResponse)
async def update_and_resend_message(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: uuid.UUID,
    message_id: uuid.UUID,
    update_data: MessageResendUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a message and regenerate all subsequent responses.
    This will delete all messages that come after the modified message.
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
    
    # Get the message to be updated
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.chat_id == chat_id
    ).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    # Check if message belongs to the user
    if message.role != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only user messages can be updated",
        )
    
    # Get the sequence number of the message
    sequence = message.sequence
    
    # Delete all subsequent messages
    db.query(Message).filter(
        Message.chat_id == chat_id,
        Message.sequence > sequence
    ).delete()
    
    # Update the message content
    message.content = update_data.new_content
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Get the updated conversation history
    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.sequence)
        .all()
    )
    
    # Format messages for the LLM
    message_history = [{"role": msg.role, "content": msg.content} for msg in messages]
    
    # Generate the assistant response
    async def generate_stream():
        # Create a placeholder for the assistant's response
        assistant_message = Message(
            chat_id=chat_id,
            role="assistant",
            content="",  # Will be updated incrementally
            sequence=sequence + 1,
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
                assistant_message.content = full_response
                db.add(assistant_message)
                db.commit()
                
            # Yield for streaming response
            yield f"data: {token}\n\n"
        
        # Update the final message
        assistant_message.content = full_response
        db.add(assistant_message)
        db.commit()
        
        yield f"data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
    ) 