from src import models
from src.config.database import Database
from src.service.Logger import logger


class ImplicitService:

    def __init__(self, db: Database):
        self.db = db

    def post_seen(self, post_id, seen_dto):
        logger.info(f"Post {post_id} seen by user {seen_dto.time_seen}")
        implicit_data = self.db.query(models.ImplicitData).filter(
                models.ImplicitData.post_id == post_id,
                models.ImplicitData.user_id == seen_dto.user_id).first()
        if implicit_data is None:
            implicit_data = self._create_implicit_data(post_id, seen_dto)

        implicit_data.time_seen = seen_dto.time_seen
        self.db.commit()

    def post_clicked(self, post_id, user_id):
        logger.info(f"Post {post_id} clicked by user {user_id}")
        implicit_data = self.db.query(models.ImplicitData).filter(
                models.ImplicitData.post_id == post_id,
                models.ImplicitData.user_id == user_id).first()
        if implicit_data is None:
            implicit_data = self._create_implicit_data(post_id, user_id)

        implicit_data.clicked = True
        self.db.commit()

    def _create_implicit_data(self, post_id, seen_dto):
        logger.info(f"Creating implicit data for post {post_id} seen by user {seen_dto.user_id}")
        implicit_data = models.ImplicitData(post_id=post_id, user_id=seen_dto.user_id)
        self.db.add(implicit_data)
        self.db.commit()
        return implicit_data
