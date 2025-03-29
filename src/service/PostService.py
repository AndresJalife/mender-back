from fastapi import HTTPException, BackgroundTasks

from src.config.database import Database
from src.model import dto
from src.models import Post, UserPostInfo, Comments
from src.service.Logger import logger

from src.service.UserService import UserService
from src.service.recommendation.RecommendationService import RecommendationService


class PostService:

    def __init__(self, db: Database, background_tasks: BackgroundTasks):
        logger.info(f"Initializing PostService")
        self.db = db
        self.user_service = UserService
        self.recommendation_service = RecommendationService(self.db, background_tasks)
        self.background_tasks = background_tasks

    def get_posts(self, user):
        logger.info(f"Getting posts for user: {user.user_id}")
        return [
            {
                "post_id": 1,
                "entity_id": 802119,
                "entity_type": 'm',
                "entity": {
                    "title": "The Shawshank Redemption",
                    "overview": "Imprisoned in the 1940s for the double murder of his wife and her lover, "
                                "upstanding banker Andy Dufresne begins a new life at the Shawshank prison, "
                                "where he puts his accounting skills to work for an amoral warden. During his"
                                " long stretch in prison, Dufresne comes to be admired by the other inmates -- "
                                "including an older prisoner named Red -- for his integrity and unquenchable sense of hope.",
                    "year": 1994,
                    "link": "xyXX8LXiNJ4",
                    "director": "Frank Darabont",
                    "screenplay": "Stephen King",
                    "genres": ["Drama", "Crime"],
                    "rating": 8.7
                },
                "likes": 40,
                "liked": True,
                "seen": False,
                "comments": 3
            },
            {
                "post_id": 2,
                "entity_id": 802114,
                "entity_type": 'm',
                "entity": {
                    "title": "Flow",
                    "overview": "A solitary cat, displaced by a great flood, finds refuge on a boat with various species "
                                "and must navigate the challenges of adapting to a transformed world together.",
                    "year": 2024,
                    "link": "l5zSgSuIDU4",
                    "director": "Gints Zilbalodis",
                    "screenplay": "Matīss Kaža",
                    "genres": ["Animation", "Fantasy", "Adventure"],
                    "rating": 8.3
                },
                "likes": 15,
                "liked": False,
                "seen": True,
                "comments": 0
            }
        ]

        # entity_ids = self.recommendation_service.get_recommendation(user.user_id)
        # logger.info(f"Getting posts: {entity_ids}")
        # # [802119, 441130, 278154, 414419, 381289, 446893, 679, 637, 431580, 417859]
        # posts = []
        # for entity_id in entity_ids:
        #     posts.append(self.get_post_by_entity(entity_id, 'm'))
        # return posts

    def create_post(self, request: dto.Post):
        try:
            db_post = Post(**request.dict())
            self.db.add(db_post)
            self.db.commit()
        except Exception as e:
            logger.error(f"Error creating user {request.entity_id}: {e}")
            raise HTTPException(detail={'message': f'{e}'}, status_code=400)

    def get_post(self, post_id):
        logger.info(f"Getting post: {post_id}")
        post = self.db.query(Post).filter(Post.post_id == post_id).first()
        if post is None:
            raise HTTPException(status_code=404, detail="El Post no se ha encontrado.")
        return post

    def get_post_by_entity(self, entity_id, entity_type):
        logger.info(f"Getting post: {entity_id}")
        post = self.db.query(Post).filter((Post.entity_id == entity_id) and (Post.entity_type == entity_type)).first()
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

        if not user_post_info.liked:
            user_post_info.liked = True
        else:
            user_post_info.liked = False

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

        if not user_post_info.seen:
            user_post_info.seen = True
        else:
            user_post_info.seen = False

        self.db.commit()

    def search_posts(self, q):
        #         search for posts with q in title or director
        logger.info(f"Searched for posts: {q}")
        return [
            {
                "post_id": 1,
                "entity_id": 802119,
                "entity_type": 'm',
                "entity": {
                    "title": "The Shawshank Redemption",
                    "overview": "Imprisoned in the 1940s for the double murder of his wife and her lover, "
                                "upstanding banker Andy Dufresne begins a new life at the Shawshank prison, "
                                "where he puts his accounting skills to work for an amoral warden. During his"
                                " long stretch in prison, Dufresne comes to be admired by the other inmates -- "
                                "including an older prisoner named Red -- for his integrity and unquenchable sense of hope.",
                    "year": 1994,
                    "link": "xyXX8LXiNJ4",
                    "director": "Frank Darabont",
                    "screenplay": "Stephen King",
                    "genres": ["Drama", "Crime"],
                    "rating": 8.7
                },
                "likes": 40,
                "liked": True,
                "seen": False,
                "comments": 3
            },
            {
                "post_id": 2,
                "entity_id": 802114,
                "entity_type": 'm',
                "entity": {
                    "title": "Flow",
                    "overview": "A solitary cat, displaced by a great flood, finds refuge on a boat with various species "
                                "and must navigate the challenges of adapting to a transformed world together.",
                    "year": 2024,
                    "link": "l5zSgSuIDU4",
                    "director": "Gints Zilbalodis",
                    "screenplay": "Matīss Kaža",
                    "genres": ["Animation", "Fantasy", "Adventure"],
                    "rating": 8.3
                },
                "likes": 15,
                "liked": False,
                "seen": True,
                "comments": 0
            }
        ]

    def get_comments(self, post_id):
        logger.info(f"Getting comments for post: {post_id}")
        comments = self.db.query(Comments).filter(Comments.post_id == post_id).all()
        return comments

