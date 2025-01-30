from fastapi import APIRouter, HTTPException, Depends
from requests import HTTPError
from starlette.responses import JSONResponse

from ..config.database import Database, get_db
from ..config.firebase import pb
from ..model import requests, dto
from ..models import User
from ..service.ChatService import ChatService
from ..service.Logger import logger
from firebase_admin import auth as fauth
from ..service.auth import get_current_uid

chat_router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

def get_chat_service(db: Database = Depends(get_db)) -> ChatService:
    return ChatService(db)

@chat_router.get("/", description="", response_model=dto.Post)
async def get_chats(user_uuid: str = Depends(get_current_uid),
                   chat_service: ChatService = Depends(get_chat_service)):
    return chat_service.get_chats()
