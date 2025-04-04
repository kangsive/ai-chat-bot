import uuid
import pytest

from app.models.user import User
from app.models.chat import Chat, Message


class TestChatModel:
    def test_chat_creation(self, db_session):
        """Test basic chat creation."""
        # Create a user first
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword123"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create a chat
        chat = Chat(
            title="Test Chat",
            user_id=user.id,
            model="gpt-4"
        )
        db_session.add(chat)
        db_session.commit()
        
        # Query the chat back
        db_chat = db_session.query(Chat).filter(Chat.title == "Test Chat").first()
        
        assert db_chat is not None
        assert db_chat.title == "Test Chat"
        assert db_chat.user_id == user.id
        assert db_chat.model == "gpt-4"
        assert db_chat.is_archived is False
        
        # Check relationship
        assert db_chat.user.username == "testuser"
        
        # Ensure timestamps are created
        assert db_chat.created_at is not None
        assert db_chat.updated_at is not None
    
    def test_chat_with_no_title(self, db_session):
        """Test chat creation with no title."""
        # Create a user first
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword123"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create a chat without title
        chat = Chat(
            user_id=user.id,
            model="gpt-3.5-turbo"
        )
        db_session.add(chat)
        db_session.commit()
        
        # Query the chat back
        db_chat = db_session.query(Chat).filter(Chat.user_id == user.id).first()
        
        assert db_chat is not None
        assert db_chat.title is None
        assert db_chat.model == "gpt-3.5-turbo"


class TestMessageModel:
    def test_message_creation(self, db_session):
        """Test message creation and association with chat."""
        # Create a user first
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword123"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create a chat
        chat = Chat(
            title="Test Chat",
            user_id=user.id,
            model="gpt-4"
        )
        db_session.add(chat)
        db_session.commit()
        
        # Create messages
        message1 = Message(
            chat_id=chat.id,
            role="user",
            content="Hello, how are you?",
            sequence=1
        )
        
        message2 = Message(
            chat_id=chat.id,
            role="assistant",
            content="I'm doing well, thank you! How can I help you today?",
            sequence=2,
            tokens=15
        )
        
        db_session.add_all([message1, message2])
        db_session.commit()
        
        # Query the messages back
        db_messages = db_session.query(Message).filter(
            Message.chat_id == chat.id
        ).order_by(Message.sequence).all()
        
        assert len(db_messages) == 2
        
        # Check first message
        assert db_messages[0].role == "user"
        assert db_messages[0].content == "Hello, how are you?"
        assert db_messages[0].sequence == 1
        assert db_messages[0].tokens is None
        
        # Check second message
        assert db_messages[1].role == "assistant"
        assert db_messages[1].content == "I'm doing well, thank you! How can I help you today?"
        assert db_messages[1].sequence == 2
        assert db_messages[1].tokens == 15
        
        # Check relationship
        assert db_messages[0].chat.title == "Test Chat"
        
    def test_message_with_metadata(self, db_session):
        """Test message creation with metadata."""
        # Create a user first
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword123"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create a chat
        chat = Chat(
            title="Test Chat",
            user_id=user.id
        )
        db_session.add(chat)
        db_session.commit()
        
        # Create a message with metadata
        message = Message(
            chat_id=chat.id,
            role="assistant",
            content="This is a response with metadata",
            sequence=1,
            tokens=8,
            message_metadata={
                "model": "gpt-4",
                "finish_reason": "stop",
                "processing_time": 1.25
            }
        )
        
        db_session.add(message)
        db_session.commit()
        
        # Query the message back
        db_message = db_session.query(Message).filter(
            Message.chat_id == chat.id
        ).first()
        
        assert db_message is not None
        assert db_message.message_metadata["model"] == "gpt-4"
        assert db_message.message_metadata["finish_reason"] == "stop"
        assert db_message.message_metadata["processing_time"] == 1.25
    
    def test_chat_message_cascade_delete(self, db_session):
        """Test that messages are deleted when their chat is deleted."""
        # Create a user first
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword123"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create a chat
        chat = Chat(
            title="Test Chat",
            user_id=user.id
        )
        db_session.add(chat)
        db_session.commit()
        
        # Create messages
        message1 = Message(
            chat_id=chat.id,
            role="user",
            content="Message 1",
            sequence=1
        )
        
        message2 = Message(
            chat_id=chat.id,
            role="assistant",
            content="Message 2",
            sequence=2
        )
        
        db_session.add_all([message1, message2])
        db_session.commit()
        
        # Verify messages exist
        message_count = db_session.query(Message).filter(
            Message.chat_id == chat.id
        ).count()
        assert message_count == 2
        
        # Delete the chat
        db_session.delete(chat)
        db_session.commit()
        
        # Verify messages are deleted
        remaining_messages = db_session.query(Message).filter(
            Message.chat_id == chat.id
        ).count()
        assert remaining_messages == 0 