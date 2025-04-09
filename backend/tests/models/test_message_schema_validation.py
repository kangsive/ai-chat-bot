import uuid
import pytest
from datetime import datetime

from app.models.user import User
from app.models.chat import Chat, Message, MessageRole, Attachment
from app.schemas.chat import Message as MessageSchema
from sqlalchemy.exc import IntegrityError


class TestMessageSchemaValidation:
    """Test cases to ensure Message model objects correctly validate against the Pydantic schema."""
    
    def setup_method(self, method):
        """Create test data to be used for all tests."""
        self.test_user_data = {
            "email": f"test-{uuid.uuid4()}@example.com",
            "username": f"testuser-{uuid.uuid4()}",
            "hashed_password": "hashedpassword123",
            "full_name": "Test User"
        }
        
    def create_test_user(self, db_session):
        """Create and return a test user."""
        user = User(**self.test_user_data)
        db_session.add(user)
        db_session.commit()
        return user
    
    def test_basic_message_schema_validation(self, db_session):
        """Test that a basic message can be validated against the schema."""
        # Create a User and Chat
        user = self.create_test_user(db_session)
        chat = Chat(title="Test Chat", user_id=user.id)
        db_session.add(chat)
        db_session.commit()
        
        # Create a simple user message
        message = Message.create_user_message(
            chat_id=chat.id,
            content="This is a test message",
            sequence=1
        )
        db_session.add(message)
        db_session.commit()
        
        # Query the message back
        db_message = db_session.query(Message).filter(Message.id == message.id).first()
        
        # Convert to dict using model_dump
        message_dict = db_message.model_dump()
        
        # Validate with Pydantic schema
        try:
            message_schema = MessageSchema(**message_dict)
            validation_successful = True
        except Exception as e:
            validation_successful = False
            pytest.fail(f"Message schema validation failed: {str(e)}")
        
        assert validation_successful
        assert message_schema.id == message.id
        assert message_schema.chat_id == chat.id
        assert message_schema.role == "user"
        assert message_schema.content == "This is a test message"
        assert message_schema.sequence == 1
    
    def test_tool_message_schema_validation(self, db_session):
        """Test that a tool message can be validated against the schema."""
        # Create a User and Chat
        user = self.create_test_user(db_session)
        chat = Chat(title="Test Chat", user_id=user.id)
        db_session.add(chat)
        db_session.commit()
        
        # Create a tool message with text content
        # Note: Using string instead of structured content now
        message = Message.create_tool_message(
            chat_id=chat.id,
            content="Result of the tool call",  # Plain text content
            tool_call_id="call_12345",
            sequence=2
        )
        db_session.add(message)
        db_session.commit()
        
        # Query the message back
        db_message = db_session.query(Message).filter(Message.id == message.id).first()
        
        # Convert to dict using model_dump
        message_dict = db_message.model_dump()
        
        # Debug print
        print(f"Tool message dict: {message_dict}")
        
        # Validate with Pydantic schema
        try:
            message_schema = MessageSchema(**message_dict)
            validation_successful = True
        except Exception as e:
            validation_successful = False
            pytest.fail(f"Tool message schema validation failed: {str(e)}")
        
        assert validation_successful
        assert message_schema.id == message.id
        assert message_schema.chat_id == chat.id
        assert message_schema.role == "tool"
        assert message_schema.content == "Result of the tool call"
        assert message_schema.sequence == 2
    
    def test_structured_tool_message_schema_validation(self, db_session):
        """Test that a tool message with structured content can be validated against the schema."""
        # Create a User and Chat
        user = self.create_test_user(db_session)
        chat = Chat(title="Test Chat", user_id=user.id)
        db_session.add(chat)
        db_session.commit()
        
        # Create a tool message with structured content
        structured_content = [
            {"type": "text", "text": "Result line 1"},
            {"type": "text", "text": "Result line 2"}
        ]
        
        message = Message.create_tool_message(
            chat_id=chat.id,
            content=structured_content,
            tool_call_id="call_12345",
            sequence=3
        )
        db_session.add(message)
        db_session.commit()
        
        # Query the message back
        db_message = db_session.query(Message).filter(Message.id == message.id).first()
        
        # Convert to dict using model_dump
        message_dict = db_message.model_dump()
        
        # Debug print
        print(f"Structured tool message dict: {message_dict}")
        
        # Validate with Pydantic schema
        try:
            message_schema = MessageSchema(**message_dict)
            validation_successful = True
        except Exception as e:
            validation_successful = False
            pytest.fail(f"Structured tool message schema validation failed: {str(e)}")
        
        assert validation_successful
        assert message_schema.id == message.id
        assert message_schema.chat_id == chat.id
        assert message_schema.role == "tool"
        # Check that content was flattened correctly
        assert "Result line 1" in message_schema.content
        assert "Result line 2" in message_schema.content
        assert message_schema.sequence == 3
    
    def test_message_with_attachments_schema_validation(self, db_session):
        """Test that a message with attachments can be validated against the schema."""
        # Create a User and Chat
        user = self.create_test_user(db_session)
        chat = Chat(title="Test Chat", user_id=user.id)
        db_session.add(chat)
        db_session.commit()
        
        # Create a user message
        message = Message.create_user_message(
            chat_id=chat.id,
            content="Check this image",
            sequence=1
        )
        db_session.add(message)
        db_session.commit()
        
        # Add an attachment to the message
        attachment = Attachment(
            message_id=message.id,
            filename="test.png",
            file_path="/tmp/test.png",
            file_type="image/png",
            file_size=1024
        )
        db_session.add(attachment)
        db_session.commit()
        
        # Query the message with attachment
        db_message = db_session.query(Message).filter(Message.id == message.id).first()
        
        # Convert to dict using model_dump
        message_dict = db_message.model_dump()
        
        # Validate with Pydantic schema
        try:
            message_schema = MessageSchema(**message_dict)
            validation_successful = True
        except Exception as e:
            validation_successful = False
            pytest.fail(f"Message with attachments schema validation failed: {str(e)}")
        
        assert validation_successful
        assert message_schema.id == message.id
        assert message_schema.role == "user"
        assert message_schema.content == "Check this image"
        assert len(message_schema.attachments) == 1
        assert message_schema.attachments[0].filename == "test.png"
        assert message_schema.attachments[0].file_type == "image/png" 