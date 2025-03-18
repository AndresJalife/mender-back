from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks

from ..config.database import Database, get_db
from ..model import dto
from ..models import User
from ..service.PostService import PostService
from ..service.auth import authenticate_and_get_user

post_router = APIRouter(
        prefix="/post",
        tags=["Post"],
)


def get_post_service(background_tasks: BackgroundTasks, db: Database = Depends(get_db)) -> PostService:
    return PostService(db, background_tasks)


@post_router.get("", description="Gets n posts for a specific user",
                 response_model=List[dto.Post])
async def get_posts(user: User = Depends(authenticate_and_get_user),
                    post_service: PostService = Depends(get_post_service)):
    return post_service.get_posts(user)

@post_router.post("", description="Creates a new post", response_model=None)
async def create_post(request: dto.Post,
                      user: User = Depends(authenticate_and_get_user),
                      post_service: PostService = Depends(get_post_service)):
    post_service.create_post(request)

@post_router.get("/{post_id}", description="Gets details of a post", response_model=dto.Post)
async def get_post(post_id: str, user: User = Depends(authenticate_and_get_user),
                   post_service: PostService = Depends(get_post_service)):
    return post_service.get_post(post_id)


@post_router.post("/{post_id}/like", description="Likes a post",
                  status_code=200, response_model=None)
async def like_post(post_id: str, user: User = Depends(authenticate_and_get_user),
                    post_service: PostService = Depends(get_post_service)):
    return post_service.like_post(post_id, user)


@post_router.post("/{post_id}/comment", description="Comments a post",
                  status_code=200, response_model=None)
async def comment_post(comment: dto.Comment,
                       post_id: str,
                       user: User = Depends(authenticate_and_get_user),
                       post_service: PostService = Depends(get_post_service)):
    return post_service.comment_post(post_id, user, comment)


@post_router.post("/{post_id}/rate", description="Rates a post",
                  response_model=None, status_code=200)
async def rate_post(rate: dto.Rate,
                    post_id: str,
                    user: User = Depends(authenticate_and_get_user),
                    post_service: PostService = Depends(get_post_service)):
    return post_service.rate_post(post_id, user, rate)


@post_router.post("/{post_id}/see", description="Saves if the user has seen a post",
                  response_model=None, status_code=200)
async def see_post(post_id: str,
                   user: User = Depends(authenticate_and_get_user),
                   post_service: PostService = Depends(get_post_service)):
    return post_service.see_post(post_id, user)

