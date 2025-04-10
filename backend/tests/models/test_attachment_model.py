import os
import uuid
import tempfile
import pytest
from pathlib import Path

from app.models.user import User
from app.models.chat import Chat, Message, Attachment, MessageRole, FileType


class TestAttachmentModel:
    def setup_method(self, method):
        """Setup for each test."""
        # Create test user data
        self.test_user_data = {
            "email": f"test-{uuid.uuid4()}@example.com",
            "username": f"testuser-{uuid.uuid4()}",
            "hashed_password": "hashedpassword123",
            "full_name": "Test User"
        }
        
        # Create temp directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a test image file
        self.image_path = Path(self.temp_dir.name) / "test_image.jpg"
        with open(self.image_path, "wb") as f:
            f.write(b"fake image content")
            
        # Create a test document file
        self.doc_path = Path(self.temp_dir.name) / "test_doc.pdf"
        with open(self.doc_path, "wb") as f:
            f.write(b"fake PDF content")
    
    def teardown_method(self, method):
        """Cleanup after each test."""
        self.temp_dir.cleanup()
    
    def create_test_user(self, db_session):
        """Create and return a test user."""
        user = User(**self.test_user_data)
        db_session.add(user)
        db_session.commit()
        return user
    
    def create_test_chat(self, db_session, user):
        """Create and return a test chat."""
        chat = Chat(
            title="Test Chat",
            user_id=user.id
        )
        db_session.add(chat)
        db_session.commit()
        return chat
    
    def test_attachment_creation(self, db_session):
        """Test basic attachment creation."""
        # Create user and chat
        user = self.create_test_user(db_session)
        chat = self.create_test_chat(db_session, user)
        
        # Create a message with an attachment
        message = Message.create_user_message(
            chat_id=chat.id,
            content="Here's an image",
            sequence=1
        )
        db_session.add(message)
        db_session.commit()
        
        # Create an attachment
        attachment = Attachment(
            message_id=message.id,
            filename="test_image.jpg",
            file_path=str(self.image_path),
            file_type="image/jpeg",
            file_size=os.path.getsize(self.image_path)
        )
        db_session.add(attachment)
        db_session.commit()
        
        # Query the attachment back
        db_attachment = db_session.query(Attachment).filter(
            Attachment.message_id == message.id
        ).first()
        
        # Verify the attachment properties
        assert db_attachment is not None
        assert db_attachment.filename == "test_image.jpg"
        assert db_attachment.file_path == str(self.image_path)
        assert db_attachment.file_type == "image/jpeg"
        assert db_attachment.file_size == os.path.getsize(self.image_path)
        
        # Verify relationship to message
        assert db_attachment.message.role == MessageRole.USER
        assert db_attachment.message.content == "Here's an image"
        
        # Test file_category property
        assert db_attachment.file_category == FileType.IMAGE
    
    def test_message_with_multiple_attachments(self, db_session):
        """Test a message with multiple attachments."""
        # Create user and chat
        user = self.create_test_user(db_session)
        chat = self.create_test_chat(db_session, user)
        
        # Create a message
        message = Message.create_user_message(
            chat_id=chat.id,
            content="Here are some files",
            sequence=1
        )
        db_session.add(message)
        db_session.commit()
        
        # Create multiple attachments
        attachments = [
            Attachment(
                message_id=message.id,
                filename="test_image.jpg",
                file_path=str(self.image_path),
                file_type="image/jpeg",
                file_size=os.path.getsize(self.image_path)
            ),
            Attachment(
                message_id=message.id,
                filename="test_doc.pdf",
                file_path=str(self.doc_path),
                file_type="application/pdf",
                file_size=os.path.getsize(self.doc_path)
            )
        ]
        db_session.add_all(attachments)
        db_session.commit()
        
        # Query the message with attachments
        db_message = db_session.query(Message).filter(
            Message.id == message.id
        ).first()
        
        # Verify the message has the attachments
        assert db_message is not None
        assert len(db_message.attachments) == 2
        
        # Check the file types
        file_types = {attachment.file_type for attachment in db_message.attachments}
        assert "image/jpeg" in file_types
        assert "application/pdf" in file_types
        
        # Check file categories
        file_categories = {attachment.file_category for attachment in db_message.attachments}
        assert FileType.IMAGE in file_categories
        assert FileType.DOCUMENT in file_categories
        
    def test_message_to_openai_format_with_attachments(self, db_session, monkeypatch):
        """Test the to_openai_format method with attachments."""
        # Create user and chat
        user = self.create_test_user(db_session)
        chat = self.create_test_chat(db_session, user)
        
        # Create a message
        message = Message.create_user_message(
            chat_id=chat.id,
            content="Check out this image",
            sequence=1
        )
        db_session.add(message)
        db_session.commit()
        
        # Create an attachment
        attachment = Attachment(
            message_id=message.id,
            filename="test_image.jpg",
            file_path=str(self.image_path),
            file_type="image/jpeg",
            file_size=os.path.getsize(self.image_path)
        )
        db_session.add(attachment)
        db_session.commit()
        
        # Mock the base64 encoding to avoid file I/O issues in tests
        def mock_process_attachments(self, base_content):
            content_list = list(base_content) if base_content else []
            content_list.append({
                'type': 'image_url',
                'image_url': {
                    'url': f"data:image/jpeg;base64,mockbase64data"
                }
            })
            return content_list
        
        # Apply the monkeypatch
        monkeypatch.setattr(Message, '_process_attachments', mock_process_attachments)
        
        # Query the message back
        db_message = db_session.query(Message).filter(
            Message.id == message.id
        ).first()
        
        # Get the OpenAI format
        openai_format = db_message.to_openai_format()
        
        # Verify the content includes the attachment
        assert isinstance(openai_format["content"], list)
        assert len(openai_format["content"]) == 2  # Text + image
        assert openai_format["content"][0]["type"] == "text"
        assert openai_format["content"][0]["text"] == "Check out this image"
        assert openai_format["content"][1]["type"] == "image_url"
        assert "mockbase64data" in openai_format["content"][1]["image_url"]["url"]
    
    def test_attachment_cascade_delete(self, db_session):
        """Test that attachments are deleted when their message is deleted."""
        # Create user and chat
        user = self.create_test_user(db_session)
        chat = self.create_test_chat(db_session, user)
        
        # Create a message
        message = Message.create_user_message(
            chat_id=chat.id,
            content="Here's a file",
            sequence=1
        )
        db_session.add(message)
        db_session.commit()
        
        # Create an attachment
        attachment = Attachment(
            message_id=message.id,
            filename="test_doc.pdf",
            file_path=str(self.doc_path),
            file_type="application/pdf",
            file_size=os.path.getsize(self.doc_path)
        )
        db_session.add(attachment)
        db_session.commit()
        
        # Verify attachment exists
        attachment_count = db_session.query(Attachment).filter(
            Attachment.message_id == message.id
        ).count()
        assert attachment_count == 1
        
        # Delete the message
        db_session.delete(message)
        db_session.commit()
        
        # Verify attachment is deleted
        remaining_attachments = db_session.query(Attachment).filter(
            Attachment.message_id == message.id
        ).count()
        assert remaining_attachments == 0 