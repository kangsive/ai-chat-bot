import uuid
import pytest
from datetime import datetime

from app.models.user import User
from app.models.chat import Chat, Message, MessageRole, ContentType
from sqlalchemy.exc import IntegrityError

class TestMessageModel:
    def setup_method(self, method):
        """Create a test user to be used for all tests."""
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
        
    def test_create_message_with_text_content(self, db_session):
        """Test creating a message with simple text content."""
        # Create a User first
        user = self.create_test_user(db_session)
        
        # Create a Chat linked to the user
        chat = Chat(
            title="Test Chat",
            user_id=user.id
        )
        db_session.add(chat)
        db_session.commit()
        
        # Create a Message with text content
        message = Message.create_user_message(
            chat_id=chat.id,
            content="Hello, how are you?",  # Simple text content
            sequence=1
        )
        db_session.add(message)
        db_session.commit()
        
        # Query the message back
        db_message = db_session.query(Message).filter(Message.id == message.id).first()
        
        # Verify the message properties
        assert db_message is not None
        assert db_message.chat_id == chat.id
        assert db_message.role == MessageRole.USER
        assert db_message.sequence == 1
        assert db_message.content == "Hello, how are you?"
        assert isinstance(db_message._content, dict)
        assert "content" in db_message._content
        assert db_message._content["content"][0]["type"] == "text"
        assert db_message._content["content"][0]["text"] == "Hello, how are you?"
        
        # Verify to_openai_format works
        openai_format = db_message.to_openai_format()
        assert openai_format["role"] == "user"
        assert openai_format["content"] == "Hello, how are you?"
        
    def test_create_message_with_structured_content(self, db_session):
        """Test creating a message with structured content (list of content objects)."""
        # Create a User first
        user = self.create_test_user(db_session)
        
        # Create a Chat linked to the user
        chat = Chat(
            title="Test Chat",
            user_id=user.id
        )
        db_session.add(chat)
        db_session.commit()
        
        # Create structured content
        structured_content = [
            {
                "type": "text",
                "text": "What are in these images? Is there any difference between them?"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/image1.jpg"
                }
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/image2.jpg"
                }
            }
        ]
        
        # Create a Message with structured content
        message = Message.create_user_message(
            chat_id=chat.id,
            content=structured_content,  # Structured content
            sequence=1
        )
        db_session.add(message)
        db_session.commit()
        
        # Query the message back
        db_message = db_session.query(Message).filter(Message.id == message.id).first()
        
        # Verify the message properties
        assert db_message is not None
        assert db_message.chat_id == chat.id
        assert db_message.role == MessageRole.USER
        assert db_message.sequence == 1
        assert isinstance(db_message.content, list)
        assert db_message._content["content"] == structured_content
        
        # Verify to_openai_format works
        openai_format = db_message.to_openai_format()
        assert openai_format["role"] == "user"
        assert openai_format["content"] == structured_content
        assert len(openai_format["content"]) == 3
        assert openai_format["content"][0]["type"] == "text"
        assert openai_format["content"][1]["type"] == "image_url"
        
    def test_message_content_validation(self, db_session):
        """Test that message content validation works correctly."""
        # Create a User first
        user = self.create_test_user(db_session)
        
        # Create a Chat linked to the user
        chat = Chat(
            title="Test Chat",
            user_id=user.id
        )
        db_session.add(chat)
        db_session.commit()
        
        # Try to create a message with invalid content
        with pytest.raises(ValueError) as excinfo:
            message = Message(
                chat_id=chat.id,
                role=MessageRole.USER,
                sequence=1,
                _content={"invalid": "content"}  # Invalid content structure
            )
            db_session.add(message)
            db_session.commit()
            
        assert "Message content must be a dict with a 'content' field" in str(excinfo.value)
        db_session.rollback()
        
    def test_system_message_creation(self, db_session):
        """Test creating a system message."""
        # Create a User first
        user = self.create_test_user(db_session)
        
        # Create a Chat linked to the user
        chat = Chat(
            title="Test Chat",
            user_id=user.id
        )
        db_session.add(chat)
        db_session.commit()
        
        # Create a system message
        message = Message.create_system_message(
            chat_id=chat.id,
            content="You are a helpful assistant.",
            sequence=1
        )
        db_session.add(message)
        db_session.commit()
        
        # Query the message back
        db_message = db_session.query(Message).filter(Message.id == message.id).first()
        
        # Verify the message properties
        assert db_message is not None
        assert db_message.role == MessageRole.SYSTEM
        assert db_message.content == "You are a helpful assistant."
        
        # Verify to_openai_format works
        openai_format = db_message.to_openai_format()
        assert openai_format["role"] == "system"
        assert openai_format["content"] == "You are a helpful assistant."
        
    def test_assistant_message_with_tool_calls(self, db_session):
        """Test creating an assistant message with tool calls."""
        # Create a User first
        user = self.create_test_user(db_session)
        
        # Create a Chat linked to the user
        chat = Chat(
            title="Test Chat",
            user_id=user.id
        )
        db_session.add(chat)
        db_session.commit()
        
        # Create tool calls
        tool_calls = [
            {
                "id": "call_abc123",
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"location": "New York", "unit": "celsius"}'
                }
            }
        ]
        
        # Create an assistant message with tool calls
        message = Message.create_assistant_message(
            chat_id=chat.id,
            content="I'll check the weather for you.",
            sequence=1,
            tool_calls=tool_calls
        )
        db_session.add(message)
        db_session.commit()
        
        # Query the message back
        db_message = db_session.query(Message).filter(Message.id == message.id).first()
        
        # Verify the message properties
        assert db_message is not None
        assert db_message.role == MessageRole.ASSISTANT
        assert db_message.content == "I'll check the weather for you."
        assert db_message.tool_calls is not None
        assert len(db_message.tool_calls) == 1
        assert db_message.tool_calls[0]["id"] == "call_abc123"
        assert db_message.tool_calls[0]["function"]["name"] == "get_weather"
        
        # Verify to_openai_format works
        openai_format = db_message.to_openai_format()
        assert openai_format["role"] == "assistant"
        assert openai_format["content"] == "I'll check the weather for you."
        assert "tool_calls" in openai_format
        assert openai_format["tool_calls"][0]["id"] == "call_abc123"
        
    def test_tool_message_creation(self, db_session):
        """Test creating a tool message."""
        # Create a User first
        user = self.create_test_user(db_session)
        
        # Create a Chat linked to the user
        chat = Chat(
            title="Test Chat",
            user_id=user.id
        )
        db_session.add(chat)
        db_session.commit()
        
        # Create a tool message
        message = Message.create_tool_message(
            chat_id=chat.id,
            content="The weather in New York is 22°C and sunny.",
            tool_call_id="call_abc123",
            sequence=1
        )
        db_session.add(message)
        db_session.commit()
        
        # Query the message back
        db_message = db_session.query(Message).filter(Message.id == message.id).first()
        
        # Verify the message properties
        assert db_message is not None
        assert db_message.role == MessageRole.TOOL
        assert db_message.content == "The weather in New York is 22°C and sunny."
        assert db_message.tool_call_id == "call_abc123"
        
        # Verify to_openai_format works
        openai_format = db_message.to_openai_format()
        assert openai_format["role"] == "tool"
        assert openai_format["content"] == "The weather in New York is 22°C and sunny."
        assert openai_format["tool_call_id"] == "call_abc123"
        
    def test_from_openai_format(self, db_session):
        """Test creating messages from OpenAI format."""
        # Create a User first
        user = self.create_test_user(db_session)
        
        # Create a Chat linked to the user
        chat = Chat(
            title="Test Chat",
            user_id=user.id
        )
        db_session.add(chat)
        db_session.commit()
        
        # OpenAI format messages
        openai_messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "What's the weather like?"
            },
            {
                "role": "assistant",
                "content": "I'll check the weather for you.",
                "tool_calls": [
                    {
                        "id": "call_abc123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "New York"}'
                        }
                    }
                ]
            },
            {
                "role": "tool",
                "content": "The weather in New York is 22°C and sunny.",
                "tool_call_id": "call_abc123"
            }
        ]
        
        # Create messages from OpenAI format
        messages = []
        for i, msg_data in enumerate(openai_messages):
            message = Message.from_openai_format(msg_data, chat.id, i+1)
            messages.append(message)
        
        db_session.add_all(messages)
        db_session.commit()
        
        # Query the messages back
        db_messages = db_session.query(Message).filter(
            Message.chat_id == chat.id
        ).order_by(Message.sequence).all()
        
        # Verify the messages
        assert len(db_messages) == 4
        
        # System message
        assert db_messages[0].role == MessageRole.SYSTEM
        assert db_messages[0].content == "You are a helpful assistant."
        
        # User message
        assert db_messages[1].role == MessageRole.USER
        assert db_messages[1].content == "What's the weather like?"
        
        # Assistant message with tool calls
        assert db_messages[2].role == MessageRole.ASSISTANT
        assert db_messages[2].content == "I'll check the weather for you."
        assert db_messages[2].tool_calls is not None
        assert db_messages[2].tool_calls[0]["function"]["name"] == "get_weather"
        
        # Tool message
        assert db_messages[3].role == MessageRole.TOOL
        assert db_messages[3].content == "The weather in New York is 22°C and sunny."
        assert db_messages[3].tool_call_id == "call_abc123" 