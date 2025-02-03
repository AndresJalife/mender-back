from fastapi import HTTPException
from starlette.responses import JSONResponse

from src.config.database import Database
from src.config.firebase import pb
from src.models import User
from src.service.Logger import logger
from requests import HTTPError

from firebase_admin import auth as fauth

from src.service.UserService import UserService


class ChatService:

    def __init__(self, db: Database):
        self.db = db

    def get_chats(self, user):
        pass

    def get_chat(self, chat_id):
        pass
