import uuid
import pytest
from datetime import datetime, timedelta

from app.models.user import User, VerificationToken, PasswordResetToken, LoginAudit


class TestUserModel:
    def test_user_creation(self, db_session):
        """Test basic user creation."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword123",
            full_name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        
        # Query the user back from DB
        db_user = db_session.query(User).filter(User.email == "test@example.com").first()
        
        assert db_user is not None
        assert db_user.email == "test@example.com"
        assert db_user.username == "testuser"
        assert db_user.hashed_password == "hashedpassword123"
        assert db_user.full_name == "Test User"
        assert db_user.is_active is True
        assert db_user.is_superuser is False
        assert db_user.is_verified is False
        
        # Ensure timestamps are created
        assert db_user.created_at is not None
        assert db_user.updated_at is not None
    
    def test_user_unique_constraints(self, db_session):
        """Test that email and username must be unique."""
        # Create first user
        user1 = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword123"
        )
        db_session.add(user1)
        db_session.commit()
        
        # Create second user with same email
        user2 = User(
            email="test@example.com",
            username="differentuser",
            hashed_password="hashedpassword123"
        )
        db_session.add(user2)
        
        # Should raise an integrity error
        with pytest.raises(Exception):
            db_session.commit()
        
        db_session.rollback()
        
        # Create third user with same username
        user3 = User(
            email="different@example.com",
            username="testuser",
            hashed_password="hashedpassword123"
        )
        db_session.add(user3)
        
        # Should raise an integrity error
        with pytest.raises(Exception):
            db_session.commit()
            
        db_session.rollback()


class TestVerificationTokenModel:
    def test_verification_token_creation(self, db_session):
        """Test verification token creation and association with user."""
        # Create a user first
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword123"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create a verification token
        token = VerificationToken(
            token="abc123",
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db_session.add(token)
        db_session.commit()
        
        # Query the token back
        db_token = db_session.query(VerificationToken).filter(VerificationToken.token == "abc123").first()
        
        assert db_token is not None
        assert db_token.token == "abc123"
        assert db_token.user_id == user.id
        assert db_token.expires_at > datetime.utcnow()
        
        # Check relationship
        assert db_token.user.email == "test@example.com"


class TestPasswordResetTokenModel:
    def test_password_reset_token_creation(self, db_session):
        """Test password reset token creation and association with user."""
        # Create a user first
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword123"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create a password reset token
        token = PasswordResetToken(
            token="reset123",
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db_session.add(token)
        db_session.commit()
        
        # Query the token back
        db_token = db_session.query(PasswordResetToken).filter(
            PasswordResetToken.token == "reset123"
        ).first()
        
        assert db_token is not None
        assert db_token.token == "reset123"
        assert db_token.user_id == user.id
        assert db_token.expires_at > datetime.utcnow()
        
        # Check relationship
        assert db_token.user.email == "test@example.com"


class TestLoginAuditModel:
    def test_login_audit_creation(self, db_session):
        """Test login audit creation and association with user."""
        # Create a user first
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword123"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create a login audit
        audit = LoginAudit(
            user_id=user.id,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            success=True
        )
        db_session.add(audit)
        db_session.commit()
        
        # Query the audit back
        db_audit = db_session.query(LoginAudit).filter(
            LoginAudit.user_id == user.id
        ).first()
        
        assert db_audit is not None
        assert db_audit.user_id == user.id
        assert db_audit.ip_address == "192.168.1.1"
        assert db_audit.user_agent == "Mozilla/5.0"
        assert db_audit.success is True
        
        # Check relationship
        assert db_audit.user.email == "test@example.com"
        
    def test_login_audit_with_failed_login(self, db_session):
        """Test login audit with failed login attempt."""
        # Create a user first
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword123"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create a failed login audit
        audit = LoginAudit(
            user_id=user.id,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            success=False
        )
        db_session.add(audit)
        db_session.commit()
        
        # Query the audit back
        db_audit = db_session.query(LoginAudit).filter(
            LoginAudit.user_id == user.id
        ).first()
        
        assert db_audit is not None
        assert db_audit.success is False 