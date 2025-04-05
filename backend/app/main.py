import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import engine
from app.models.base import Base
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.core.logging_config import configure_logging

# Configure logging for the entire application
configure_logging()

# Create application logger
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

#Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    allow_origins=settings.BACKEND_CORS_ORIGINS
    logger.info(f"Allow origins: {allow_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Create tables on startup
@app.on_event("startup")
def create_tables():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Initialize database with default data
    logger.info("Initializing database with default data...")
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    logger.info("Database initialization complete")


@app.get("/")
def root():
    """
    Root endpoint that returns basic API information.
    """
    return {
        "message": "Welcome to the AI Chatbot API",
        "docs_url": "/docs",
        "version": "0.1.0",
    } 