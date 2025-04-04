import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.config import SystemConfig
from app.models.user import User


logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    """
    Initialize the database with essential data.
    """
    # Create a superuser if it doesn't exist
    user = db.query(User).filter(User.email == settings.EMAIL_TEST_USER).first()
    if not user:
        user = User(
            email=settings.EMAIL_TEST_USER,
            username="admin",
            hashed_password=get_password_hash("password"),  # Change in production!
            full_name="Admin User",
            is_superuser=True,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        logger.info("Created admin user")
    
    # Add system configurations if they don't exist
    configs = [
        {
            "key": "default_llm_model",
            "value": settings.LLM_MODEL,
            "description": "Default LLM model to use for chat responses",
        },
        {
            "key": "system_prompt",
            "value": "You are a helpful AI assistant.",
            "description": "Default system prompt for new chats",
        },
    ]
    
    for config_data in configs:
        config = db.query(SystemConfig).filter(
            SystemConfig.key == config_data["key"]
        ).first()
        
        if not config:
            config = SystemConfig(**config_data)
            db.add(config)
            db.commit()
            logger.info(f"Created system config: {config_data['key']}")


def main() -> None:
    """
    Main function to run database initialization.
    """
    logger.info("Creating initial data")
    db = SessionLocal()
    init_db(db)
    logger.info("Initial data created")


if __name__ == "__main__":
    main() 