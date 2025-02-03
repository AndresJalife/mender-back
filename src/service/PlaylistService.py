from src.config.database import Database


class PlaylistService:

    def __init__(self, db: Database):
        self.db = db

    def save_playlist(self, playlist_id):
        pass

    def remove_post_from_playlist(self, playlist_id, post_id):
        pass

    def add_post_to_playlist(self, playlist_id, post_id):
        pass

    def get_saved_playlists(self, user):
        pass

    def get_playlist(self, playlist_id, user):
        pass

    def create_playlist(self, user, playlist_dto):
        pass
