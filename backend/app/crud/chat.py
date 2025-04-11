from typing import Any, Dict, List, Optional, Union
import uuid
from sqlalchemy.orm import Session

from app.models.chat import Chat, Message, Attachment, MessageRole
from app.schemas.chat import ChatCreate, ChatUpdate, MessageCreate

class CRUDChat:
    def get_user_chats(self, db: Session, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Chat]:
        """Get all chats for a user."""
        chats = (
            db.query(Chat)
            .filter(Chat.user_id == user_id)
            .order_by(Chat.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return chats
    
    def create(self, db: Session, *, obj_in: ChatCreate, user_id: uuid.UUID) -> Chat:
        """Create a new chat."""
        chat = Chat(
            user_id=user_id,
            title=obj_in.title,
            model=obj_in.model,
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat
    
    def get(self, db: Session, *, chat_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Chat]:
        """Get a specific chat by id."""
        return db.query(Chat).filter(
            Chat.id == chat_id, Chat.user_id == user_id
        ).first()
    
    def update(self, db: Session, *, db_obj: Chat, obj_in: Union[ChatUpdate, Dict[str, Any]]) -> Chat:
        """Update a chat."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, chat_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a chat."""
        chat = self.get(db, chat_id=chat_id, user_id=user_id)
        if not chat:
            return False
        db.delete(chat)
        db.commit()
        return True
    
    def get_messages(self, db: Session, *, chat_id: uuid.UUID) -> List[Message]:
        """Get all messages for a chat."""
        return (
            db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.sequence)
            .all()
        )
    
    def get_message(self, db: Session, *, message_id: uuid.UUID, chat_id: uuid.UUID) -> Optional[Message]:
        """Get a specific message."""
        return db.query(Message).filter(
            Message.id == message_id, Message.chat_id == chat_id
        ).first()
    
    def get_message_by_sequence(self, db: Session, *, sequence: int, chat_id: uuid.UUID) -> Optional[Message]:
        """Get a specific message by sequence."""
        return db.query(Message).filter(
            Message.sequence == sequence, Message.chat_id == chat_id
        ).first()
    
    def create_message(self, db: Session, *, obj_in: MessageCreate, chat_id: uuid.UUID) -> Message:
        """Create a new message."""
        message = Message(
            chat_id=chat_id,
            role=obj_in.role,
            _content={"content": obj_in.content},
            sequence=obj_in.sequence,
            message_metadata=obj_in.message_metadata,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    
    def update_message(self, db: Session, *, db_obj: Message, content: Dict, message_metadata: Dict = None) -> Message:
        """Update a message."""
        db_obj._content = content
        if message_metadata:
            db_obj.message_metadata = message_metadata
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete_messages_after_sequence(self, db: Session, *, chat_id: uuid.UUID, sequence: int) -> int:
        """Delete all messages after a specific sequence.
        
        Returns:
            int: Number of messages deleted
        """
        # First get all messages to be deleted
        messages_to_delete = db.query(Message).filter(
            Message.chat_id == chat_id,
            Message.sequence > sequence
        ).all()
        
        # Count messages for return value
        count = len(messages_to_delete)
        
        # Delete each message object individually to trigger cascade
        for message in messages_to_delete:
            db.delete(message)
        
        db.commit()
        return count
    
    def get_attachments(self, db: Session, *, message_id: uuid.UUID) -> List[Attachment]:
        """Get all attachments for a message."""
        return db.query(Attachment).filter(
            Attachment.message_id == message_id
        ).all()
    
    def get_attachment(self, db: Session, *, attachment_id: uuid.UUID) -> Optional[Attachment]:
        """Get a specific attachment."""
        return db.query(Attachment).filter(
            Attachment.id == attachment_id
        ).first()
    
    def create_attachment(
        self, db: Session, *, message_id: uuid.UUID, filename: str, file_path: str, file_type: str, file_size: int
    ) -> Attachment:
        """Create a new attachment."""
        attachment = Attachment(
            message_id=message_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
        )
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        return attachment
    
    def delete_attachment(self, db: Session, *, attachment_id: uuid.UUID) -> bool:
        """Delete an attachment."""
        attachment = self.get_attachment(db, attachment_id=attachment_id)
        if not attachment:
            return False
        db.delete(attachment)
        db.commit()
        return True
    
    def update_assistant_message(
        self, db: Session, *, message_id: uuid.UUID, content: str, is_complete: bool = False
    ) -> Message:
        """Update an assistant message with new content."""
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return None
            
        message._content = {"content": [{"type": "text", "text": content}]}
        if is_complete:
            message.is_complete = True
            
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

chat = CRUDChat() 