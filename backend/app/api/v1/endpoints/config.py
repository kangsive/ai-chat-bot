from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.api import deps
from app.models.config import SystemConfig, UserConfig
from app.models.user import User
from app.crud.config import system_config, user_config
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
    config = user_config.get_or_create(db, user_id=current_user.id)
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
    config = user_config.get_by_user_id(db, user_id=current_user.id)
    
    if not config:
        # Create config if none exists
        config = user_config.create(db, user_id=current_user.id, preferences=config_in.preferences)
        return config
    
    # Update existing config
    updated_config = user_config.update(db, db_obj=config, obj_in=config_in)
    return updated_config


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
    configs = system_config.get_all(db, skip=skip, limit=limit)
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
    existing_config = system_config.get_by_key(db, key=config_in.key)
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Config with key '{config_in.key}' already exists",
        )
    
    config = system_config.create(db, obj_in=config_in)
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
    config = system_config.get_by_key(db, key=key)
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
    config = system_config.get_by_key(db, key=key)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config not found",
        )
    
    updated_config = system_config.update(db, db_obj=config, obj_in=config_in)
    return updated_config


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
    config = system_config.get_by_key(db, key=key)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config not found",
        )
    
    system_config.delete(db, key=key)
    return {"message": "Config deleted successfully"} 