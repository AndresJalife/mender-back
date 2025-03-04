from typing import List

from fastapi import APIRouter, Depends

from ..config.database import Database, get_db
from ..model import dto
from ..models import User
from ..service.ChatService import ChatService
from ..service.auth import authenticate_and_get_user

chat_router = APIRouter(
        prefix="/chat",
        tags=["Chat"],
)


def get_chat_service(db: Database = Depends(get_db)) -> ChatService:
    return ChatService(db)


# @chat_router.get("/list", description="Gets the list of chats", response_model=dto.ChatList)
# async def get_chats(user: User = Depends(authenticate_and_get_user),
#                     chat_service: ChatService = Depends(get_chat_service)):
#     return chat_service.get_chats(user)

@chat_router.get("/", description="Gets the bot chat", response_model=List[dto.Message])
async def get_chat(user: User = Depends(authenticate_and_get_user),
                   chat_service: ChatService = Depends(get_chat_service)):
    return chat_service.get_chat(user)


@chat_router.post("/message", description="Sends a message to the chat", response_model=dto.Message)
async def send_message(message: dto.Message, user: User = Depends(authenticate_and_get_user),
                       chat_service: ChatService = Depends(get_chat_service)):
    return chat_service.send_message(user, message)
