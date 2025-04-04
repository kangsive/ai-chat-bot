from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class User(Base):
    """User model for authentication and profile information."""
    
    __tablename__ = "users"  # Changed from default "user" to avoid PostgreSQL keyword conflict
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile info
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(String(20), default="client", nullable=False)  # 'engineer' or 'client'
    
    # Email verification
    is_verified = Column(Boolean, default=False)
    
    # Relationships
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    login_audits = relationship("LoginAudit", back_populates="user", cascade="all, delete-orphan")
    verification_tokens = relationship("VerificationToken", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    configs = relationship("UserConfig", back_populates="user", cascade="all, delete-orphan")

    # Add check constraint for role
    __table_args__ = (
        CheckConstraint(role.in_(["engineer", "client"]), name="check_user_role"),
    )


class VerificationToken(Base):
    """Email verification tokens for users."""
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(255), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Updated foreign key reference
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(hours=24))
    
    # Relationships
    user = relationship("User", back_populates="verification_tokens")


class PasswordResetToken(Base):
    """Password reset tokens for users."""
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(255), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Updated foreign key reference
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(hours=1))
    
    # Relationships
    user = relationship("User", back_populates="password_reset_tokens")


class LoginAudit(Base):
    """Tracks user login activity for security purposes."""
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Updated foreign key reference
    ip_address = Column(String(45), nullable=False)  # IPv6 can be up to 45 chars
    user_agent = Column(String(255))
    success = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="login_audits") 