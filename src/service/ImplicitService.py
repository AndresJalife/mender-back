from src.config.database import Database


class ImplicitService:

    def __init__(self, db: Database):
        self.db = db

    def post_seen(self, post_id, seen_dto):
        pass
