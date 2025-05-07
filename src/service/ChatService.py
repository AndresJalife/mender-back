from src import models
from src.config.database import Database
from src.model import dto
from src.models import ChatHistory
from src.service.Logger import logger
from src.service.chatbot.GroqService import GroqService


class ChatService:

    def __init__(self, db: Database):
        self.db = db
        self.groq_service = GroqService(db)

    def get_chats(self, user):
        logger.info(f"Getting chats for user {user.user_id}")
        chats = self.db.query(ChatHistory).filter(ChatHistory.user_id == user.user_id).all()
        if not chats:
            return []

        return chats

    def get_chat(self, user):
        logger.info(f"Getting chat for user {user.user_id}")
        chat = self.db.query(ChatHistory).filter(ChatHistory.user_id == user.user_id).all()
        if not chat:
            return []

        return chat

    async def send_message(self, user, message):
        logger.info(f"Sending message from user {user.user_id}")
        next_order = self._save_message(user, message)
        return await self._get_bot_message(user, message, next_order)

    def _save_message(self, user, message):
        last_message = self._get_last_message(user)
        order = 1
        if last_message:
            order = last_message.order + 1

        next_message = ChatHistory(
            user_id=user.user_id,
            message=message.message,
            order=order,
            bot_made=False
        )

        self.db.add(next_message)
        self.db.commit()

        return next_message.order + 1

    def _get_last_message(self, user):
        return self.db.query(ChatHistory).filter(ChatHistory.user_id == user.user_id).order_by(
            ChatHistory.order.desc()).first()

    async def _get_bot_message(self, user, message, next_order):
        history = self._load_history(user)
        return_message = await self.groq_service.generate(user, history, message.message)

        return dto.Message(
            bot_made=True,
            order=next_order,
            message=return_message
         )

    def _load_history(self, user, limit: int = 10) -> list[dict]:
        """
        Returns the last *limit* messages in OpenAI format:
        [{"role":"system","content":...}, {"role":"user",...}, ...]
        """
        rows = (
            self.db.query(ChatHistory)
            .filter(ChatHistory.user_id == user.user_id)
            .order_by(ChatHistory.order.desc())
            .limit(limit)
            .all()
        )
        return [
            {"role": "assistant" if r.bot_made else "user", "content": r.message}
            for r in reversed(rows)
        ]