from src.config.database import Database
from src.service.Logger import logger


class ChatService:

    def __init__(self, db: Database):
        self.db = db

    def get_chats(self, user):
        pass

    def get_chat(self, chat_id):
        pass
