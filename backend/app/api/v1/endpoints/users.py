import uuid
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User, LoginAudit, VerificationToken, PasswordResetToken
from app.crud.user import user
from app.schemas.user import (
    User as UserSchema,
    UserCreate,
    UserUpdate,
    Token,
    Login,
    PasswordReset,
    PasswordResetConfirm,
    EmailVerify
)

router = APIRouter()


@router.post("/", response_model=UserSchema)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create a new user.
    """
    # Check if user with same email or username exists
    existing_user = user.get_by_email_or_username(db, email=user_in.email, username=user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email or username already exists."
        )
    
    # Create new user
    db_user = user.create(db, obj_in=user_in)
    
    # Generate verification token (would send email in production)
    verification_token = user.create_verification_token(db, user_id=db_user.id)
    
    return db_user


@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
    client_ip: str = "127.0.0.1",  # Would extract from request in production
    user_agent: str = "Unknown",  # Would extract from request in production
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # Authenticate user
    db_user = user.authenticate(db, username_or_email=form_data.username, password=form_data.password)
    
    login_success = db_user is not None
    user_id = db_user.id if db_user else uuid.uuid4()
    
    # Log the login attempt
    user.create_login_audit(
        db, 
        user_id=user_id,
        ip_address=client_ip,
        user_agent=user_agent,
        success=login_success
    )
    
    if not login_success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active(db_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    # Create access token
    access_token = create_access_token(subject=str(db_user.id))
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserSchema)
def read_user_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.put("/me", response_model=UserSchema)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    user_in: UserUpdate,
) -> Any:
    """
    Update own user.
    """
    if user_in.username and user_in.username != current_user.username:
        # Check if username is already taken
        existing_user = user.get_by_email_or_username(db, username=user_in.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
    
    if user_in.email and user_in.email != current_user.email:
        # Check if email is already taken
        existing_user = user.get_by_email_or_username(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Update user
    updated_user = user.update(db, db_obj=current_user, obj_in=user_in)
    
    return updated_user


@router.post("/verify-email", response_model=UserSchema)
def verify_email(
    *,
    db: Session = Depends(deps.get_db),
    email_verification: EmailVerify,
) -> Any:
    """
    Verify a user's email with token.
    """
    token = user.get_verification_token(db, token=email_verification.token)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    db_user = db.query(User).filter(User.id == token.user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify user
    verified_user = user.verify_user(db, user=db_user, token=token)
    
    return verified_user


@router.post("/reset-password")
def request_password_reset(
    *,
    db: Session = Depends(deps.get_db),
    password_reset: PasswordReset,
) -> Any:
    """
    Request a password reset.
    """
    db_user = user.get_by_email_or_username(db, email=password_reset.email)
    
    if not db_user:
        # Don't reveal that the user doesn't exist
        return {"message": "If the email exists, a reset link will be sent"}
    
    # Create reset token
    reset_token = user.create_password_reset_token(db, user_id=db_user.id)
    
    # In production, would send an email with the reset link
    
    return {"message": "If the email exists, a reset link will be sent"}


@router.post("/reset-password/confirm")
def confirm_password_reset(
    *,
    db: Session = Depends(deps.get_db),
    password_reset: PasswordResetConfirm,
) -> Any:
    """
    Reset a user's password using a token.
    """
    token = user.get_password_reset_token(db, token=password_reset.token)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    db_user = db.query(User).filter(User.id == token.user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Reset password
    updated_user = user.reset_password(db, user=db_user, token=token, new_password=password_reset.new_password)
    
    return {"message": "Password reset successfully"} 