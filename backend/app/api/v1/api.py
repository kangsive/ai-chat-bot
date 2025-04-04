from fastapi import APIRouter

from app.api.v1.endpoints import chat, config, users

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chat.router, prefix="/chats", tags=["chats"])
api_router.include_router(config.router, prefix="/config", tags=["config"]) 