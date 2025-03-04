from fastapi import HTTPException, BackgroundTasks

from src.config.database import Database
from src.models import Post, UserPostInfo, Comments
from src.service.Logger import logger

from src.service.UserService import UserService
from src.service.recommendation.RecommendationService import RecommendationService


class PostService:

    def __init__(self, db: Database, background_tasks: BackgroundTasks):
        self.db = db
        self.user_service = UserService
        self.recommendation_service = RecommendationService(self.db)
        self.background_tasks = background_tasks

    def get_posts(self, user):
        logger.info(f"Getting posts for user: {user.id}")
        return self.recommendation_service.get_recommendation(user.user_id)

    def get_post(self, post_id):
        logger.info(f"Getting post: {post_id}")
        post = self.db.query(Post).filter(Post.post_id == post_id).first()
        if post is None:
            raise HTTPException(status_code=404, detail="El Post no se ha encontrado.")
        return post

    def like_post(self, post_id, user):
        logger.info(f"Liking post: {post_id} for user: {user.id}")
        self.background_tasks.add_task(self._sum_to_post_likes, post_id)
        self.background_tasks.add_task(self._like_user_post, post_id, user)

    def comment_post(self, post_id, user, comment):
        logger.info(f"Commenting post: {post_id} for user: {user.id}")
        self.background_tasks.add_task(self._sum_to_post_comments, post_id)
        self.background_tasks.add_task(self._comment_user_post, post_id, user, comment)

    def rate_post(self, post_id, user, rate):
        logger.info(f"Rating post: {post_id} for user: {user.id}")
        self.background_tasks.add_task(self._rate_user_post, post_id, user, rate.rating)

    def see_post(self, post_id, user):
        logger.info(f"Seeing post: {post_id} for user: {user.id}")
        self.background_tasks.add_task(self._see_user_post, post_id, user)

    def _sum_to_post_likes(self, post_id):
        post = self.db.query(Post).filter(Post.post_id == post_id).first()
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")
        post.likes += 1
        self.db.commit()

    def _like_user_post(self, post_id, user):
        user_post_info = self.get_or_create_post_info(post_id, user)
        user_post_info.liked = True
        self.db.commit()

    def get_or_create_post_info(self, post_id, user):
        user_post_info = self.db.query(UserPostInfo).filter(UserPostInfo.post_id == post_id).first()

        if user_post_info is None:
            user_post_info = UserPostInfo(user_id=user.id, post_id=post_id)

        self.db.add(user_post_info)
        return user_post_info

    def _sum_to_post_comments(self, post_id):
        post = self.db.query(Post).filter(Post.post_id == post_id).first()
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")
        post.comments += 1
        self.db.commit()

    def _comment_user_post(self, post_id, user, comment):
        comment = Comments(user_id=user.id, post_id=post_id, comment=comment.comment)
        self.db.add(comment)
        self.db.commit()

    def _rate_user_post(self, post_id, user, rating):
        user_post_info = self.get_or_create_post_info(post_id, user)
        user_post_info.user_rating = rating
        self.db.commit()

    def _see_user_post(self, post_id, user):
        user_post_info = self.get_or_create_post_info(post_id, user)
        user_post_info.seen = True
        self.db.commit()
