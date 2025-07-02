from datetime import datetime, timedelta
from typing import Type

from starlette.concurrency import run_in_threadpool

from src.config.database import Database
from src.model import dto
from src.models import ChatHistory
from src.service.ImplicitService import ImplicitService
from src.service.Logger import logger
from src.service.chatbot.GrokServiceV2 import GrokServiceV2
from src.service.recommendation.RecommendationService import recommendation_service
from src.util.util import str_to_datetime


class ChatService:

    def __init__(self, db: Database, backgroun_tasks):
        self.db = db
        self.groq_service = GrokServiceV2(db, recommendation_service)
        self.implicit_service = ImplicitService(db)
        self.background_tasks = backgroun_tasks

    def get_chat(self, user):
        logger.info(f"Getting chat for user {user.user_id}")
        chat = self.db.query(ChatHistory).filter(ChatHistory.user_id == user.user_id).all()
        if not chat:
            return []

        return chat

    async def send_message(self, user, message):
        next_order, chat_id = await run_in_threadpool(self._save_message, user, message)
        history = await run_in_threadpool(self._load_history, user, chat_id)

        bot_reply, entities_tuple = await self.groq_service.generate(user=user, history=history, text=message.message)

        logger.info(f"Bot reply: {bot_reply}")

        await run_in_threadpool(self._save_bot_reply, user, bot_reply, next_order, chat_id)

        self.implicit_service.chat_recommendations_given(
            user, entities_tuple
        )

        # self.background_tasks.add_task(
        #     self.implicit_service.chat_recommendations_given,
        #     user, entities_tuple
        # )

        return dto.Message(bot_made=True, order=next_order, message=bot_reply)

    def _save_message(self, user, message):
        last_message = self._get_last_message(user)
        order = 1
        chat_id = 1
        if last_message:
            order = last_message.order + 1
            chat_id = self._get_chat_id(last_message)

        next_message = ChatHistory(
            user_id=user.user_id,
            message=message.message,
            order=order,
            chat_id=chat_id,
            bot_made=False
        )

        self.db.add(next_message)

        return next_message.order + 1, next_message.chat_id

    def _get_chat_id(self, last_message: Type[ChatHistory]):
        last_30_minutes = datetime.now() - timedelta(minutes=30)

        created = last_message.created_date
        if isinstance(created, str):
            created = str_to_datetime(created)

        if created < last_30_minutes:
            return last_message.chat_id + 1

        return last_message.chat_id

    def _get_last_message(self, user):
        return self.db.query(ChatHistory).filter(ChatHistory.user_id == user.user_id).order_by(
            ChatHistory.order.desc()).first()

    def _load_history(self, user, chat_id) -> list[dict]:
        """
        Returns the last *limit* messages in OpenAI format:
        [{"role":"system","content":...}, {"role":"user",...}, ...]
        """
        rows : list[Type[ChatHistory]] = (
            self.db.query(ChatHistory)
            .filter(ChatHistory.user_id == user.user_id,
                    ChatHistory.chat_id == chat_id)
            .order_by(ChatHistory.order.desc())
            .all()
        )

        return [
            {"role": "assistant" if r.bot_made else "user", "content": r.message}
            for r in reversed(rows)
        ]

    # helper extracted for clarity
    def _save_bot_reply(self, user, reply, order, chat_id):
        self.db.add(ChatHistory(
            user_id=user.user_id,
            message=reply,
            order=order,
            chat_id=chat_id,
            bot_made=True
        ))
        self.db.commit()