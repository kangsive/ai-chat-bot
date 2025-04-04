import uuid
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User, LoginAudit, VerificationToken, PasswordResetToken
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
    user = db.query(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)
    ).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email or username already exists."
        )
    
    # Create new user
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=True,
        is_superuser=False,
        is_verified=False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Generate verification token (would send email in production)
    verification_token = VerificationToken(
        token=str(uuid.uuid4()),
        user_id=db_user.id,
    )
    db.add(verification_token)
    db.commit()
    
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
    # Check if user exists
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()
    
    login_success = False
    
    if user and verify_password(form_data.password, user.hashed_password):
        login_success = True
        # Create access token
        access_token = create_access_token(subject=str(user.id))
    
    # Log the login attempt
    login_audit = LoginAudit(
        user_id=user.id if user else uuid.uuid4(),  # Use random ID if user not found
        ip_address=client_ip,
        user_agent=user_agent,
        success=login_success,
    )
    db.add(login_audit)
    db.commit()
    
    if not login_success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
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
        existing_user = db.query(User).filter(User.username == user_in.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
    
    if user_in.email and user_in.email != current_user.email:
        # Check if email is already taken
        existing_user = db.query(User).filter(User.email == user_in.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    user_data = user_in.dict(exclude_unset=True)
    
    if user_in.password:
        user_data["hashed_password"] = get_password_hash(user_in.password)
        del user_data["password"]
    
    for field, value in user_data.items():
        setattr(current_user, field, value)
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/verify-email", response_model=UserSchema)
def verify_email(
    *,
    db: Session = Depends(deps.get_db),
    email_verification: EmailVerify,
) -> Any:
    """
    Verify a user's email with token.
    """
    token = db.query(VerificationToken).filter(
        VerificationToken.token == email_verification.token
    ).first()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    user = db.query(User).filter(User.id == token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_verified = True
    db.delete(token)  # Remove the used token
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/reset-password")
def request_password_reset(
    *,
    db: Session = Depends(deps.get_db),
    password_reset: PasswordReset,
) -> Any:
    """
    Request a password reset.
    """
    user = db.query(User).filter(User.email == password_reset.email).first()
    
    if not user:
        # Don't reveal that the user doesn't exist
        return {"message": "If the email exists, a reset link will be sent"}
    
    # Delete any existing reset tokens for the user
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).delete()
    
    # Create new reset token
    reset_token = PasswordResetToken(
        token=str(uuid.uuid4()),
        user_id=user.id,
    )
    db.add(reset_token)
    db.commit()
    
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
    token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == password_reset.token
    ).first()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    user = db.query(User).filter(User.id == token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.hashed_password = get_password_hash(password_reset.new_password)
    db.delete(token)  # Remove the used token
    db.commit()
    db.refresh(user)
    
    return {"message": "Password has been reset successfully"} 