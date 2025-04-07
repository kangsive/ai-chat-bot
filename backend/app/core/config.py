import os
import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from dotenv import load_dotenv

load_dotenv(override=True)


class Settings(BaseSettings):
    """Application settings configuration."""
    
    # API settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS settings - origins allowed to make requests
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"] # allow frontend to make requests
    
    @field_validator("BACKEND_CORS_ORIGINS", mode='before')
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database settings
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ai_chatbot")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    DATABASE_URI: Optional[PostgresDsn] = None
    
    @field_validator("DATABASE_URI", mode='before')
    def assemble_db_connection(cls, v: Optional[str], info: Any) -> Any:
        if isinstance(v, str):
            return v
            
        postgres_server = cls.model_fields["POSTGRES_SERVER"].default
        postgres_user = cls.model_fields["POSTGRES_USER"].default
        postgres_password = cls.model_fields["POSTGRES_PASSWORD"].default
        postgres_port = cls.model_fields["POSTGRES_PORT"].default
        postgres_db = cls.model_fields["POSTGRES_DB"].default
        
        # Override with actual values from environment if set
        for field in ["POSTGRES_SERVER", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_PORT", "POSTGRES_DB"]:
            env_value = os.getenv(field)
            if env_value:
                if field == "POSTGRES_SERVER":
                    postgres_server = env_value
                elif field == "POSTGRES_USER":
                    postgres_user = env_value
                elif field == "POSTGRES_PASSWORD":
                    postgres_password = env_value
                elif field == "POSTGRES_PORT":
                    postgres_port = env_value
                elif field == "POSTGRES_DB":
                    postgres_db = env_value
        
        # In Pydantic v2, we construct the URL string directly
        db_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_server}:{postgres_port}/{postgres_db}"
        return db_url
    
    # Email configuration
    EMAILS_ENABLED: bool = False
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[EmailStr] = None
    EMAIL_TEST_USER: Optional[EmailStr] = "test@example.com"
    
    # LLM Configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", "openai/gpt-3.5-turbo")
    LLM_API_KEY: Optional[str] = os.getenv("LLM_API_KEY")
    
    # File storage configuration
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/tmp/uploads")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB default
    ALLOWED_EXTENSIONS: List[str] = [
        "pdf", "txt", "doc", "docx", "xls", "xlsx", 
        "jpg", "jpeg", "png", "gif", "mp3", "mp4"
    ]
    
    # Project name
    PROJECT_NAME: str = "AI Chatbot"
    
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings() 