from src import models
from src.config.database import Database
from src.models import User
from src.service.Logger import logger
from src.service.rating_calculator.RatingCalculator import RatingCalculator, Feedback, FeedbackType


class ImplicitService:

    def __init__(self, db: Database):
        self.db = db

    def post_seen(self, user, post_id, seen_dto, background_tasks):
        logger.info(f"Post {post_id} seen by user {seen_dto.time_seen}")
        background_tasks.add_task(self._post_seen, post_id, user.user_id, seen_dto)
        background_tasks.add_task(self._set_new_user_as_not_new, user)

    def _set_new_user_as_not_new(self, user: User):
        logger.info(f"user is new?: {user}")
        if user.new:
            logger.info(f"Setting user: {user.user_id} as not new")
            user.new = False
            self.db.commit()

    def _post_seen(self, post_id, user_id, seen_dto):
        implicit_data = self.db.query(models.ImplicitData).filter(
                models.ImplicitData.post_id == post_id,
                models.ImplicitData.user_id == user_id).first()
        if implicit_data is None:
            implicit_data = self._create_implicit_data(post_id, user_id)

        implicit_data.time_seen = seen_dto.time_seen
        if seen_dto.time_seen < 1000:
            logger.info(f"Post {post_id} not seen enough time")
            return
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
        self._save_calculated_rating(implicit_data)
        self.db.commit()


    def chat_recommendations_given(self, user, recommendations: tuple[str, str, int]):
        for _, __, post_id in recommendations:
            implicit_data = self.db.query(models.ImplicitData).filter(
                    models.ImplicitData.post_id == post_id,
                    models.ImplicitData.user_id == user.user_id).first()
            if implicit_data is None:
                implicit_data = self._create_implicit_data(post_id, user.user_id)

            implicit_data.chat_recommended = True
            # self._save_calculated_rating(implicit_data)
        self.db.commit()

    def _save_calculated_rating(self, implicit_data):
        logger.info(f"Saving calculated rating for post {implicit_data.post_id} seen by user {implicit_data.user_id}")

        user_post_info = self.db.query(models.UserPostInfo).filter(
                models.UserPostInfo.post_id == implicit_data.post_id,
                models.UserPostInfo.user_id == implicit_data.user_id).first()

        if user_post_info is None:
            user_post_info = models.UserPostInfo(post_id=implicit_data.post_id, user_id=implicit_data.user_id)
            self.db.add(user_post_info)

        rating = self._calculate_implicit_rating(implicit_data, user_post_info)

        if rating is None:
            logger.error(f"Rating is None for post {implicit_data.post_id} seen by user {implicit_data.user_id}")
            return

        calculated_rating = self.db.query(models.CalculatedRating).filter(
                models.CalculatedRating.post_id == implicit_data.post_id,
                models.CalculatedRating.user_id == implicit_data.user_id).first()

        if calculated_rating is None:
            calculated_rating = models.CalculatedRating(post_id=implicit_data.post_id, user_id=implicit_data.user_id)
            self.db.add(calculated_rating)

        calculated_rating.rating = rating

    def _calculate_implicit_rating(self, implicit_data, user_post_info):
        logger.info(f"Calculating implicit rating for user {implicit_data.user_id} on post {implicit_data.post.post_id}")

        return RatingCalculator().calculate(feedbacks=[
                Feedback(FeedbackType.LIKE, value=1 if user_post_info.liked else 0),
                Feedback(FeedbackType.WATCH_SECONDS, value=implicit_data.time_seen),
                Feedback(FeedbackType.MORE_INFO, value=1 if implicit_data.clicked else 0),
                Feedback(FeedbackType.SAW_MOVIE, value=1 if user_post_info.seen else 0),
                Feedback(FeedbackType.CHATBOT_REC, value=1 if implicit_data.chat_recommended else 0),
            ], explicit_rating=user_post_info.user_rating)


    def _create_implicit_data(self, post_id, user_id):
        logger.info(f"Creating implicit data for post {post_id} seen by user {user_id}")
        implicit_data = models.ImplicitData(post_id=post_id, user_id=user_id)
        self.db.add(implicit_data)
        self.db.commit()
        return implicit_data