from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.api import deps
from app.models.config import SystemConfig, UserConfig
from app.models.user import User
from app.schemas.config import (
    SystemConfig as SystemConfigSchema,
    SystemConfigCreate,
    SystemConfigList,
    SystemConfigUpdate,
    UserConfig as UserConfigSchema,
    UserConfigCreate,
    UserConfigUpdate,
)

router = APIRouter()


# User config endpoints
@router.get("/user", response_model=UserConfigSchema)
def get_user_config(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get the current user's config.
    """
    config = db.query(UserConfig).filter(UserConfig.user_id == current_user.id).first()
    
    if not config:
        # Create default config if none exists
        config = UserConfig(
            user_id=current_user.id,
            preferences={},
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    
    return config


@router.put("/user", response_model=UserConfigSchema)
def update_user_config(
    *,
    db: Session = Depends(deps.get_db),
    config_in: UserConfigUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update the current user's config.
    """
    config = db.query(UserConfig).filter(UserConfig.user_id == current_user.id).first()
    
    if not config:
        # Create config if none exists
        config = UserConfig(
            user_id=current_user.id,
            preferences=config_in.preferences,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config
    
    # Update existing config
    update_data = config_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


# System config endpoints - Admin only
@router.get("/system", response_model=SystemConfigList)
def get_system_configs(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get all system configs.
    """
    configs = db.query(SystemConfig).offset(skip).limit(limit).all()
    return {"configs": configs}


@router.post("/system", response_model=SystemConfigSchema)
def create_system_config(
    *,
    db: Session = Depends(deps.get_db),
    config_in: SystemConfigCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new system config.
    """
    # Check if config with same key exists
    config = db.query(SystemConfig).filter(SystemConfig.key == config_in.key).first()
    if config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Config with key '{config_in.key}' already exists",
        )
    
    config = SystemConfig(
        key=config_in.key,
        value=config_in.value,
        description=config_in.description,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.get("/system/{key}", response_model=SystemConfigSchema)
def get_system_config(
    *,
    db: Session = Depends(deps.get_db),
    key: str,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get a specific system config by key.
    """
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config not found",
        )
    return config


@router.put("/system/{key}", response_model=SystemConfigSchema)
def update_system_config(
    *,
    db: Session = Depends(deps.get_db),
    key: str,
    config_in: SystemConfigUpdate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a system config.
    """
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config not found",
        )
    
    update_data = config_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.delete("/system/{key}")
def delete_system_config(
    *,
    db: Session = Depends(deps.get_db),
    key: str,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a system config.
    """
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config not found",
        )
    
    db.delete(config)
    db.commit()
    return {"message": "Config deleted successfully"} 