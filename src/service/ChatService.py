from src import models
from src.config.database import Database
from src.model import dto
from src.service.Logger import logger


class ChatService:

    def __init__(self, db: Database):
        self.db = db

    def get_chats(self, user):
        logger.info(f"Getting chats for user {user.user_id}")
        chats = self.db.query(models.ChatHistory).filter(models.ChatHistory.user_id == user.user_id).all()
        if not chats:
            return []

        return chats

    def get_chat(self, user):
        logger.info(f"Getting chat for user {user.user_id}")
        chat = self.db.query(models.ChatHistory).filter(models.ChatHistory.user_id == user.user_id).all()
        if not chat:
            return []

        return chat

    def send_message(self, user, message):
        logger.info(f"Sending message from user {user.user_id}")
        next_order = self._save_message(user, message)
        return self._get_bot_message(user, message, next_order)

    def _save_message(self, user, message):
        last_message = self._get_last_message(user)
        order = 1
        if last_message:
            order = last_message.order + 1

        next_message = models.ChatHistory(
            user_id=user.user_id,
            message=message.message,
            order=order,
            bot_made=False
        )

        self.db.add(next_message)
        self.db.commit()

        return next_message.order + 1

    def _get_last_message(self, user):
        return self.db.query(models.ChatHistory).filter(models.ChatHistory.user_id == user.user_id).order_by(
            models.ChatHistory.order.desc()).first()

    def _get_bot_message(self, user, message, next_order):
        # get next bot message, save and return
        return dto.Message(
            bot_made=True,
            order=next_order,
            message="Hello, I am a bot!"
         )

