from datetime import datetime
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, UUID4, ConfigDict


# User config schemas
class UserConfigBase(BaseModel):
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")


class UserConfigCreate(UserConfigBase):
    user_id: UUID4


class UserConfigUpdate(UserConfigBase):
    pass


class UserConfigInDBBase(UserConfigBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserConfig(UserConfigInDBBase):
    pass


# System config schemas
class SystemConfigBase(BaseModel):
    key: str = Field(..., description="The configuration key")
    value: Any = Field(..., description="The configuration value")
    description: Optional[str] = Field(None, description="Description of this configuration setting")


class SystemConfigCreate(SystemConfigBase):
    pass


class SystemConfigUpdate(BaseModel):
    value: Optional[Any] = None
    description: Optional[str] = None


class SystemConfigInDBBase(SystemConfigBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SystemConfig(SystemConfigInDBBase):
    pass


class SystemConfigList(BaseModel):
    configs: List[SystemConfig] = [] 