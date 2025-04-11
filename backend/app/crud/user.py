from typing import Any, Dict, Optional, Union, List
import uuid
from sqlalchemy.orm import Session

from app.models.user import User, LoginAudit, VerificationToken, PasswordResetToken
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate, UserUpdate

class CRUDUser:
    def get_by_email_or_username(self, db: Session, *, email: str = None, username: str = None) -> Optional[User]:
        """Get a user by email or username."""
        if email and username:
            return db.query(User).filter(
                (User.email == email) | (User.username == username)
            ).first()
        elif email:
            return db.query(User).filter(User.email == email).first()
        elif username:
            return db.query(User).filter(User.username == username).first()
        return None
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create a new user."""
        db_user = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def update(self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]) -> User:
        """Update a user."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def authenticate(self, db: Session, *, username_or_email: str, password: str) -> Optional[User]:
        """Authenticate a user."""
        user = self.get_by_email_or_username(db, email=username_or_email, username=username_or_email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def is_active(self, user: User) -> bool:
        """Check if a user is active."""
        return user.is_active
    
    def is_superuser(self, user: User) -> bool:
        """Check if a user is a superuser."""
        return user.is_superuser
    
    def create_login_audit(self, db: Session, *, user_id: uuid.UUID, ip_address: str, user_agent: str, success: bool) -> LoginAudit:
        """Create a login audit record."""
        login_audit = LoginAudit(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
        )
        db.add(login_audit)
        db.commit()
        return login_audit
    
    def create_verification_token(self, db: Session, *, user_id: uuid.UUID) -> VerificationToken:
        """Create a verification token for a user."""
        verification_token = VerificationToken(
            token=str(uuid.uuid4()),
            user_id=user_id,
        )
        db.add(verification_token)
        db.commit()
        db.refresh(verification_token)
        return verification_token
    
    def get_verification_token(self, db: Session, *, token: str) -> Optional[VerificationToken]:
        """Get a verification token."""
        return db.query(VerificationToken).filter(VerificationToken.token == token).first()
    
    def verify_user(self, db: Session, *, user: User, token: VerificationToken) -> User:
        """Mark a user as verified and delete the verification token."""
        user.is_verified = True
        db.delete(token)
        db.commit()
        db.refresh(user)
        return user
    
    def create_password_reset_token(self, db: Session, *, user_id: uuid.UUID) -> PasswordResetToken:
        """Create a password reset token for a user."""
        # Delete any existing reset tokens for the user
        db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user_id).delete()
        
        reset_token = PasswordResetToken(
            token=str(uuid.uuid4()),
            user_id=user_id,
        )
        db.add(reset_token)
        db.commit()
        db.refresh(reset_token)
        return reset_token
    
    def get_password_reset_token(self, db: Session, *, token: str) -> Optional[PasswordResetToken]:
        """Get a password reset token."""
        return db.query(PasswordResetToken).filter(PasswordResetToken.token == token).first()
    
    def reset_password(self, db: Session, *, user: User, token: PasswordResetToken, new_password: str) -> User:
        """Reset a user's password and delete the reset token."""
        user.hashed_password = get_password_hash(new_password)
        db.delete(token)
        db.commit()
        db.refresh(user)
        return user

user = CRUDUser() 