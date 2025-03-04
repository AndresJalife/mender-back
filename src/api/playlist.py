from fastapi import APIRouter, Depends

from ..config.database import Database, get_db
from ..model import dto
from ..models import User
from ..service.PlaylistService import PlaylistService
from ..service.auth import authenticate_and_get_user

playlist_router = APIRouter(
    prefix="/playlist",
    tags=["Playlist"],
)

def get_playlist_service(db: Database = Depends(get_db)) -> PlaylistService:
    return PlaylistService(db)

@playlist_router.get("/", description="", response_model=dto.Playlist)
async def get_playlists(user: User = Depends(authenticate_and_get_user),
                        playlist_service: PlaylistService = Depends(get_playlist_service)):
    return playlist_service.get_playlists(user)


@playlist_router.post("/", description="", response_model=dto.Playlist)
async def create_playlist(playlist_dto: dto.Playlist, user: User = Depends(authenticate_and_get_user),
                          playlist_service: PlaylistService = Depends(get_playlist_service)):
    return playlist_service.create_playlist(user, playlist_dto)


@playlist_router.get("/{playlist_id}", description="", response_model=dto.Playlist)
async def get_playlist(playlist_id: str, user: User = Depends(authenticate_and_get_user),
                       playlist_service: PlaylistService = Depends(get_playlist_service)):
    return playlist_service.get_playlist(playlist_id, user)


@playlist_router.get("/saved", description="", response_model=dto.Playlist)
async def get_saved_playlists(user: User = Depends(authenticate_and_get_user),
                              playlist_service: PlaylistService = Depends(get_playlist_service)):
    return playlist_service.get_saved_playlists(user)


@playlist_router.post("/{playlist_id}/post/{post_id}", description="", response_model=dto.Playlist)
async def add_post_to_playlist(playlist_id: str, post_id: str, user: User = Depends(authenticate_and_get_user),
                               playlist_service: PlaylistService = Depends(get_playlist_service)):
     return playlist_service.add_post_to_playlist(playlist_id, post_id)


@playlist_router.delete("/{playlist_id}/post/{post_id}", description="", response_model=dto.Playlist)
async def remove_post_from_playlist(playlist_id: str, post_id: str, user: User = Depends(authenticate_and_get_user),
                                    playlist_service: PlaylistService = Depends(get_playlist_service)):
        return playlist_service.remove_post_from_playlist(playlist_id, post_id)


@playlist_router.post("/{playlist_id}/saved", description="", response_model=dto.Playlist)
async def save_playlist(playlist_id: str, user: User = Depends(authenticate_and_get_user),
                        playlist_service: PlaylistService = Depends(get_playlist_service)):
        return playlist_service.save_playlist(user, playlist_id)
