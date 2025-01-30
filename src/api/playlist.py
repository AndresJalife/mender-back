from fastapi import APIRouter, HTTPException, Depends
from requests import HTTPError
from starlette.responses import JSONResponse

from ..config.database import Database, get_db
from ..config.firebase import pb
from ..model import requests, dto
from ..models import User
from ..service.Logger import logger
from firebase_admin import auth as fauth

from ..service.PlaylistService import PlaylistService
from ..service.auth import get_current_uid

playlist_router = APIRouter(
    prefix="/playlist",
    tags=["Playlist"],
)

def get_playlist_service(db: Database = Depends(get_db)) -> PlaylistService:
    return PlaylistService(db)

@playlist_router.get("/", description="", response_model=dto.Post)
async def get_playlists(user_uuid: str = Depends(get_current_uid),
                   playlist_service: PlaylistService = Depends(get_playlist_service)):
    return playlist_service.get_playlists()
