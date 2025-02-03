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

@chat_router.get("/{chat_id}", description="Gets the bot chat", response_model=dto.Chat)
async def get_chat(chat_id: str, user: User = Depends(authenticate_and_get_user),
                   chat_service: ChatService = Depends(get_chat_service)):
    return chat_service.get_chat(chat_id)

@chat_router.post("/{chat_id}/message", description="Sends a message to the chat", response_model=dto.Chat)
async def send_message(chat_id: str, message: dto.Message, user: User = Depends(authenticate_and_get_user),
                          chat_service: ChatService = Depends(get_chat_service)):
     return chat_service.send_message(chat_id, user, message)


