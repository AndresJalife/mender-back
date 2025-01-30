from fastapi import APIRouter, HTTPException, Depends
from requests import HTTPError
from starlette.responses import JSONResponse

from ..config.database import Database, get_db
from ..config.firebase import pb
from ..model import requests, dto
from ..models import User
from ..service.Logger import logger
from firebase_admin import auth as fauth

from ..service.PostService import PostService
from ..service.auth import get_current_uid

post_router = APIRouter(
    prefix="/post",
    tags=["Post"],
)

def get_post_service(db: Database = Depends(get_db)) -> PostService:
    return PostService(db)


@post_router.get("/", description="", response_model=dto.Post)
async def get_posts(user_uuid: str = Depends(get_current_uid),
                   post_service: PostService = Depends(get_post_service)):
    return post_service.get_posts()
