from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from src.enums.Countries import Countries
from src.enums.user.UserSex import UserSex


class User(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    username: Optional[str] = None
    country: Optional[Countries] = None
    new: Optional[bool] = None
    sex: Optional[UserSex] = None
    created_date: Optional[str] = None
    uid: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class Genre(BaseModel):
    entity_genre_id: Optional[int] = None
    name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class Actor(BaseModel):
    actor_id: Optional[int] = None
    name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ProductionCompany(BaseModel):
    entity_production_company_id: Optional[int] = None
    name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class WatchProvider(BaseModel):
    watch_provider_id: Optional[int] = None
    provider_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class Entity(BaseModel):
    entity_id: Optional[int] = None
    entity_type: Optional[str] = None
    tmbd_id: Optional[int] = None
    imdb_id: Optional[str] = None
    title: Optional[str] = None
    vote_average: Optional[float] = None
    release_date: Optional[str] = None
    revenue: Optional[int] = None
    runtime: Optional[int] = None
    overview: Optional[str] = None
    popularity: Optional[float] = None
    tagline: Optional[str] = None
    trailer: Optional[str] = None
    director: Optional[str] = None

    genres: Optional[List[Genre]] = None
    actors: Optional[List[Actor]] = None
    production_companies: Optional[List[ProductionCompany]] = None
    watch_providers: Optional[List[WatchProvider]] = None
    rating: Optional[float] = None
    original_language: Optional[str] = None


class UserPostInfo(BaseModel):
    liked: Optional[bool] = None
    seen: Optional[bool] = None
    user_rating: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)


class Post(BaseModel):
    post_id: Optional[int] = None
    entity_id: Optional[int] = None
    entity: Optional[Entity] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    user_post_info: Optional[UserPostInfo] = None
    created_date: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class Playlist(BaseModel):
    pass


class PostSeen(BaseModel):
    time_seen: int


class Comment(BaseModel):
    comment: str
    user: Optional[User] = None
    created_date: Optional[str] = None


class Rate(BaseModel):
    rating: float


class Message(BaseModel):
    bot_made: Optional[bool] = None
    order: Optional[int] = None
    message: str
    model_config = ConfigDict(from_attributes=True)


class PostFilters(BaseModel):
    genres: Optional[list[str]] = None
    min_release_date: Optional[str] = None
    max_release_date: Optional[str] = None
    actors: Optional[list[str]] = None
    directors: Optional[list[str]] = None
    avoid_tmdb_ids: Optional[List[int]] = None
    original_language: Optional[str] = None

    model_config = ConfigDict()