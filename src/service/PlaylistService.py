from src import models
from src.config.database import Database
from src.service.Logger import logger


class PlaylistService:

    def __init__(self, db: Database):
        self.db = db

    def create_playlist(self, user, playlist_dto):
        logger(f"Creating playlist for user {user.uid}")
        self.db.add(models.Playlist(user_id=user.user_id, **playlist_dto.dict()))
        self.db.commit()

    def save_playlist(self, user, playlist_id):
        logger(f"Saving playlist {playlist_id} for user {user.uid}")
        db_playlist = self.db.query(models.SavedPlaylist).filter(
                models.SavedPlaylist.playlist_id == playlist_id).first()
        if db_playlist is None:
            saved_playlist = models.SavedPlaylist(user_id=user.user_id, playlist_id=playlist_id)
            self.db.add(saved_playlist)
            self.db.commit()

    def add_post_to_playlist(self, playlist_id, post_id):
        logger(f"Adding post {post_id} to playlist {playlist_id}")
        db_playlist_item = self.db.query(models.PlaylistItem).filter(
                models.PlaylistItem.playlist_id == playlist_id, models.PlaylistItem.post_id == post_id).first()
        if db_playlist_item is None:
            playlist_item = models.PlaylistItem(playlist_id=playlist_id, post_id=post_id)
            self.db.add(playlist_item)
            self.db.commit()

    def remove_post_from_playlist(self, playlist_id, post_id):
        logger(f"Removing post {post_id} from playlist {playlist_id}")
        db_playlist_item = self.db.query(models.PlaylistItem).filter(
                models.PlaylistItem.playlist_id == playlist_id, models.PlaylistItem.post_id == post_id).first()
        if db_playlist_item is not None:
            self.db.delete(db_playlist_item)
            self.db.commit()

    def get_saved_playlists(self, user):
        logger(f"Getting saved playlists for user {user.uid}")
        return self.db.query(models.Playlist).filter(models.SavedPlaylist.user_id == user.user_id).all()

    def get_playlist(self, playlist_id, user):
        logger(f"Getting playlist {playlist_id} for user {user.uid}")
        return self.db.query(models.Playlist).filter(models.Playlist.playlist_id == playlist_id).first()
