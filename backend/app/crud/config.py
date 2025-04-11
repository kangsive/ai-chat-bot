from typing import Any, Dict, List, Optional, Union
import uuid
from sqlalchemy.orm import Session

from app.models.config import SystemConfig, UserConfig
from app.schemas.config import SystemConfigCreate, SystemConfigUpdate, UserConfigCreate, UserConfigUpdate

class CRUDSystemConfig:
    def get_all(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[SystemConfig]:
        """Get all system configs."""
        return db.query(SystemConfig).offset(skip).limit(limit).all()
    
    def get_by_key(self, db: Session, *, key: str) -> Optional[SystemConfig]:
        """Get a system config by key."""
        return db.query(SystemConfig).filter(SystemConfig.key == key).first()
    
    def create(self, db: Session, *, obj_in: SystemConfigCreate) -> SystemConfig:
        """Create a new system config."""
        config = SystemConfig(
            key=obj_in.key,
            value=obj_in.value,
            description=obj_in.description,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config
    
    def update(self, db: Session, *, db_obj: SystemConfig, obj_in: Union[SystemConfigUpdate, Dict[str, Any]]) -> SystemConfig:
        """Update a system config."""
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
    
    def delete(self, db: Session, *, key: str) -> bool:
        """Delete a system config."""
        config = self.get_by_key(db, key=key)
        if not config:
            return False
        db.delete(config)
        db.commit()
        return True


class CRUDUserConfig:
    def get_by_user_id(self, db: Session, *, user_id: uuid.UUID) -> Optional[UserConfig]:
        """Get a user's config."""
        return db.query(UserConfig).filter(UserConfig.user_id == user_id).first()
    
    def create(self, db: Session, *, user_id: uuid.UUID, preferences: Dict = None) -> UserConfig:
        """Create a new user config."""
        if preferences is None:
            preferences = {}
        
        config = UserConfig(
            user_id=user_id,
            preferences=preferences,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config
    
    def update(self, db: Session, *, db_obj: UserConfig, obj_in: Union[UserConfigUpdate, Dict[str, Any]]) -> UserConfig:
        """Update a user config."""
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
    
    def get_or_create(self, db: Session, *, user_id: uuid.UUID) -> UserConfig:
        """Get a user's config or create one if it doesn't exist."""
        config = self.get_by_user_id(db, user_id=user_id)
        if not config:
            return self.create(db, user_id=user_id)
        return config


system_config = CRUDSystemConfig()
user_config = CRUDUserConfig() 