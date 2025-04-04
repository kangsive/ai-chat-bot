import uuid
from typing import Any, Dict, Optional

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class UserConfig(Base):
    """User-specific configuration settings."""
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Preferences stored as JSON
    preferences = Column(JSONB, nullable=False, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="configs")


class SystemConfig(Base):
    """Global system configuration settings."""
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(JSONB, nullable=False)
    description = Column(String(255), nullable=True) 