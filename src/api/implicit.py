from typing import List

from fastapi import APIRouter, Depends

from ..config.database import Database, get_db
from ..model import dto
from ..models import User
from ..service.ImplicitService import ImplicitService
from ..service.auth import authenticate_and_get_user

implicit_router = APIRouter(
    prefix="/implicit",
    tags=["Implicit Data"],
)

def get_implicit_service(db: Database = Depends(get_db)) -> ImplicitService:
    return ImplicitService(db)


@implicit_router.post("/post/{post_id}/post_seen", description="Stores the amount of time a user has seen a post",
                 response_model=None, status_code=200)
async def post_seen(post_id: str, seen_dto: dto.PostSeen,
                    user: User = Depends(authenticate_and_get_user),
                    implicit_service: ImplicitService = Depends(get_implicit_service)):
    return implicit_service.post_seen(post_id, seen_dto)
