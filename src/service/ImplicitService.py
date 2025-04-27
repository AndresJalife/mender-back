from src import models
from src.config.database import Database
from src.service.Logger import logger


class ImplicitService:

    def __init__(self, db: Database, background_tasks):
        self.db = db
        self.background_tasks = background_tasks

    def post_seen(self, post_id, seen_dto):
        logger.info(f"Post {post_id} seen by user {seen_dto.time_seen}")
        self.background_tasks.add_task(self._post_seen, post_id, seen_dto)

    def _post_seen(self, post_id, seen_dto):
        implicit_data = self.db.query(models.ImplicitData).filter(
                models.ImplicitData.post_id == post_id,
                models.ImplicitData.user_id == seen_dto.user_id).first()
        if implicit_data is None:
            implicit_data = self._create_implicit_data(post_id, seen_dto)

        implicit_data.time_seen = seen_dto.time_seen
        self._save_calculated_rating(implicit_data)
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

    def calculate_implicit_rating(self, user_id, post: models.Post):
        logger.info(f"Calculating implicit rating for user {user_id} on post {post.post_id}")
        implicit_data = self.db.query(models.ImplicitData).filter(
                models.ImplicitData.post_id == post.post_id,
                models.ImplicitData.user_id == user_id).first()

        user_post_info = self.db.query(models.UserPostInfo).filter(
                models.UserPostInfo.post_id == post.post_id,
                models.UserPostInfo.user_id == user_id).first()

        liked = user_post_info.liked if user_post_info else False
        seen = user_id.seen if user_post_info else False
        clicked = implicit_data.clicked if implicit_data else False
        seconds_seen = implicit_data.miliseconds_seen if implicit_data else 0
        seconds_rating = self._calculate_seconds_rating(seconds_seen)

        return self._calculate_rating(liked, seen, clicked, seconds_rating)

    def _calculate_rating(self, liked, seen, clicked, seconds_rating):
        logger.info(f"Calculating rating: liked={liked}, seen={seen}, clicked={clicked}, seconds_rating={seconds_rating}")
        return min(5, (1 if seen else 0) + (3 if liked else 0) + seconds_rating + (2 if clicked else 0))

    def _create_implicit_data(self, post_id, seen_dto):
        logger.info(f"Creating implicit data for post {post_id} seen by user {seen_dto.user_id}")
        implicit_data = models.ImplicitData(post_id=post_id, user_id=seen_dto.user_id)
        self.db.add(implicit_data)
        self.db.commit()
        return implicit_data

    def _calculate_seconds_rating(self, seconds_seen):
        if seconds_seen < 2:
            return 0
        elif seconds_seen < 4:
            return 1
        elif seconds_seen < 8:
            return 2
        else:
            return 3

    def _save_calculated_rating(self, implicit_data):
        logger.info(f"Saving calculated rating for post {implicit_data.post_id} seen by user {implicit_data.user_id}")

        rating = self.calculate_implicit_rating(implicit_data.user_id, implicit_data.post)

        calculated_rating = self.db.query(models.CalculatedRating).filter(
                models.CalculatedRating.post_id == implicit_data.post_id,
                models.CalculatedRating.user_id == implicit_data.user_id).first()

        if calculated_rating is None:
            calculated_rating = models.CalculatedRating(post_id=implicit_data.post_id, user_id=implicit_data.user_id)
            self.db.add(calculated_rating)

        calculated_rating.rating = rating
