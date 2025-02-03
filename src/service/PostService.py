from fastapi import HTTPException
from starlette.responses import JSONResponse

from src.config.database import Database
from src.config.firebase import pb
from src.models import User
from src.service.Logger import logger
from requests import HTTPError

from firebase_admin import auth as fauth

from src.service.UserService import UserService


class PostService:

    def __init__(self, db: Database):
        self.db = db

    def get_posts(self, user):
        pass

    def get_post(self, post_id):
        pass

    def like_post(self, post_id, user):
        pass

    def comment_post(self, post_id, user):
        pass

    def rate_post(self, post_id, user):
        pass

    def see_post(self, post_id, user):
        pass
