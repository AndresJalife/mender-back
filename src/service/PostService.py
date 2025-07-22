import time

from fastapi import HTTPException, BackgroundTasks
from sqlalchemy.orm import joinedload, contains_eager
from sqlalchemy import func, select
from sqlalchemy.sql import literal, union_all, select

from src.config.database import Database
from src.model import dto
from src.models import Post, UserPostInfo, Comments, Entity, ImplicitData, Actor
from src.service.ImplicitService import ImplicitService
from src.service.Logger import logger
from src.service.mock_post import mock_posts
from src.service.UserService import UserService
from src.service.recommendation.RecommendationService import recommendation_service

class PostService:

    def __init__(self, db: Database, background_tasks: BackgroundTasks):
        logger.info(f"Initializing PostService")
        self.db = db
        self.user_service = UserService
        self.recommendation_service = recommendation_service
        self.background_tasks = background_tasks
        self.implicit_service = ImplicitService(db)

    def get_cold_start_posts(self):
        """Returns a list of mock posts for cold start"""
        logger.info("Getting cold start posts")
        posts = mock_posts
        return posts

    def get_posts(self, user, k, filters):
        tmbd_ids = self.recommendation_service.get_recommendation(user.user_id, filters, k)
        logger.info(f"Getting post recommendations for user: {user.user_id}")
        logger.info(f"Filters: {filters}")
        logger.info(f"Recommendations: {tmbd_ids}")
        if not tmbd_ids:
            return []

        posts = (
            self.db.query(Post)
            .join(Entity, Post.entity_id == Entity.entity_id)
            .outerjoin(UserPostInfo, (Post.post_id == UserPostInfo.post_id) & (
                    UserPostInfo.user_id == user.user_id))
            .options(
                    joinedload(Post.entity)
                    .joinedload(Entity.genres),
                    joinedload(Post.entity)
                    .joinedload(Entity.actors),
                    joinedload(Post.entity)
                    .joinedload(Entity.entity_production_companies),
                    joinedload(Post.entity)
                    .joinedload(Entity.watch_providers),
                    contains_eager(Post.user_post_info)
            )
            .filter(Entity.tmbd_id.in_(tmbd_ids))
            .all()
        )

        return posts

    def create_post(self, request: dto.Post):
        try:
            db_post = Post(**request.dict())
            self.db.add(db_post)
            self.db.commit()
        except Exception as e:
            logger.error(f"Error creating user {request.entity_id}: {e}")
            raise HTTPException(detail={'message': f'{e}'}, status_code=400)

    def get_post(self, post_id, user):
        logger.info(f"Getting post: {post_id}")
        post = (
            self.db.query(Post)
            .outerjoin(UserPostInfo, (Post.post_id == UserPostInfo.post_id) & (
                    UserPostInfo.user_id == user.user_id))
            .options(contains_eager(Post.user_post_info))
            .filter(Post.post_id == post_id)
            .first()
        )

        try:
            for info in post.user_post_info:
                logger.info(f'{info.user_id}, {info.liked}, {info.seen}, {info.user_rating}')
        except Exception as e:
            logger.info(f"Error: {e}")

        if post is None:
            raise HTTPException(status_code=404, detail="El Post no se ha encontrado.")

        self.background_tasks.add_task(self.implicit_service.post_clicked, post_id, user.user_id)

        return post

    def like_post(self, post_id, user):
        logger.info(f"Liking post: {post_id} for user: {user.user_id}")
        self.background_tasks.add_task(self._like_user_post, post_id, user)

    def comment_post(self, post_id, user, comment):
        logger.info(f"Commenting post: {post_id} for user: {user.user_id}")
        self.background_tasks.add_task(self._sum_to_post_comments, post_id)
        self.background_tasks.add_task(self._comment_user_post, post_id, user, comment)

    def rate_post(self, post_id, user, rate):
        logger.info(f"Rating post: {post_id} for user: {user.user_id}")
        self.background_tasks.add_task(self._rate_user_post, post_id, user, rate.rating)

    def see_post(self, post_id, user):
        logger.info(f"Seeing post: {post_id} for user: {user.user_id}")
        self.background_tasks.add_task(self._see_user_post, post_id, user)

    def _sum_to_post_likes(self, post_id, liked):
        post = self.db.query(Post).filter(Post.post_id == post_id).first()
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")
        post.likes += 1 if liked else -1
        self.db.commit()

    def _like_user_post(self, post_id, user):
        user_post_info = self.get_or_create_post_info(post_id, user)

        if not user_post_info.liked:
            user_post_info.liked = True
        else:
            user_post_info.liked = False

        self._sum_to_post_likes(post_id, user_post_info.liked)

        if user_post_info.liked:
            self.background_tasks.add_task(self.implicit_service.post_liked, post_id, user.user_id)

        self.db.commit()

    def get_or_create_post_info(self, post_id, user):
        user_post_info = self.db.query(UserPostInfo).filter(UserPostInfo.post_id == post_id).first()

        if user_post_info is None:
            user_post_info = UserPostInfo(user_id=user.user_id, post_id=post_id)

        self.db.add(user_post_info)
        return user_post_info

    def _sum_to_post_comments(self, post_id):
        post = self.db.query(Post).filter(Post.post_id == post_id).first()
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")
        post.comments += 1
        self.db.commit()

    def _comment_user_post(self, post_id, user, comment):
        # Add the comment to the Comments table
        comment_entry = Comments(user_id=user.user_id, post_id=post_id, comment=comment.comment)
        self.db.add(comment_entry)
        self.db.commit()

        # Send a background task to update the implicit data comments
        self._update_implicit_data_comments(post_id, user.user_id)

    def _update_implicit_data_comments(self, post_id, user_id):
        implicit_data = self.db.query(ImplicitData).filter(ImplicitData.post_id == post_id,
                                                           ImplicitData.user_id == user_id).first()

        if implicit_data is None:
            # Create a new ImplicitData entry if it doesn't exist
            implicit_data = ImplicitData(post_id=post_id, user_id=user_id, comments=1)
            self.db.add(implicit_data)
        else:
            # Increment the comments count
            implicit_data.comments = implicit_data.comments + 1 if implicit_data.comments else 1

        self.db.commit()

    def _rate_user_post(self, post_id, user, rating):
        user_post_info = self.get_or_create_post_info(post_id, user)
        user_post_info.user_rating = rating
        self.db.commit()

    def _see_user_post(self, post_id, user):
        user_post_info = self.get_or_create_post_info(post_id, user)

        if not user_post_info.seen:
            user_post_info.seen = True
        else:
            user_post_info.seen = False

        self.db.commit()

    def search_posts(self, q: str, q_type: str, k: int):
        logger.info(f"🔍 Searching posts with query: '{q}', type: '{q_type}', limit: {k}")

        imm = func.immutable_unaccent
        q_lit = q.lower()

        # Similarity expressions
        title_sim = func.similarity(imm(func.lower(Entity.title)), literal(q_lit))
        director_sim = func.similarity(imm(func.lower(Entity.director)), literal(q_lit))
        actor_sim = func.similarity(imm(func.lower(Actor.name)), literal(q_lit))

        if q_type == "title":
            base_q = self.db.query(Entity.entity_id, title_sim.label("sim")).filter(title_sim > 0.2)
        elif q_type == "director":
            base_q = self.db.query(Entity.entity_id, director_sim.label("sim")).filter(director_sim > 0.2)
        elif q_type == "actor":
            base_q = self.db.query(Actor.entity_id, actor_sim.label("sim")).filter(actor_sim > 0.2)
        else:
            # Combine and alias all with scores
            title_q = self.db.query(Entity.entity_id.label("entity_id"), title_sim.label("sim")).filter(title_sim > 0.2)
            director_q = self.db.query(Entity.entity_id.label("entity_id"), director_sim.label("sim")).filter(
                director_sim > 0.2)
            actor_q = self.db.query(Actor.entity_id.label("entity_id"), actor_sim.label("sim")).filter(actor_sim > 0.2)

            base_q = union_all(title_q, director_q, actor_q)

        # Wrap similarity results in a subquery with row numbers
        similar_q = (
            self.db.query(base_q.c.entity_id, base_q.c.sim)
            .order_by(base_q.c.sim.desc())
            .limit(k)
            .subquery()
        )

        # Now use similarity score to sort final posts
        posts = (
            self.db.query(Post)
            .join(similar_q, Post.entity_id == similar_q.c.entity_id)
            .options(
                    joinedload(Post.entity).joinedload(Entity.genres),
                    joinedload(Post.entity).joinedload(Entity.actors),
                    joinedload(Post.entity).joinedload(Entity.watch_providers),
                    joinedload(Post.user_post_info)
            )
            .order_by(similar_q.c.sim.desc())
            .limit(k)
            .all()
        )

        return posts


    def get_comments(self, post_id):
        logger.info(f"Getting comments for post: {post_id}")
        comments = self.db.query(Comments).filter(Comments.post_id == post_id).all()
        return comments
