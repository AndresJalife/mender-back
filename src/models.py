import pytz
from sqlalchemy.orm import relationship
from datetime import date, datetime
from src.config.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, UniqueConstraint, TypeDecorator, Float, \
    BigInteger, DateTime

metadata = Base.metadata
ARG_TZ = pytz.timezone("America/Argentina/Buenos_Aires")

class FormattedDate(TypeDecorator):
    impl = Date
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%d/%m/%Y').date()
            except ValueError:
                raise ValueError("Date must be in 'dd/mm/yyyy' format")
        return value

    def process_result_value(self, value, dialect):
        return value.strftime('%d/%m/%Y') if value else None

class FormattedDateTime(TypeDecorator):
    cache_ok = True
    impl = DateTime

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                # iso format
                return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                raise ValueError("Date must be in 'dd/mm/yyyy HH:MM:SS' format")
        elif isinstance(value, datetime):
            return value  # Already a datetime object, return as is
        raise ValueError("Invalid date format. Must be 'dd/mm/yyyy HH:MM:SS' string or `datetime` object.")

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.strftime('%d/%m/%Y %H:%M:%S')
        raise ValueError("Unexpected value type returned from database.")

class User(Base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True, name="user_id", autoincrement=True)
    uid = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    country = Column(String)
    new = Column(Boolean)
    sex = Column(String)
    language = Column(String)
    username = Column(String)
    name = Column(String, nullable=False)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    comments = relationship("Comments", back_populates="user")
    user_post_info = relationship("UserPostInfo", back_populates="user")
    playlist = relationship("Playlist", back_populates="user")
    saved_playlist = relationship("SavedPlaylist", back_populates="user")
    implicit_data = relationship("ImplicitData", back_populates="user")
    chat_history = relationship("ChatHistory", back_populates="user")
    calculated_rating = relationship("CalculatedRating", back_populates="user")


class Post(Base):
    __tablename__ = 'post'

    post_id = Column(Integer, primary_key=True, name="post_id", autoincrement=True)
    entity_id = Column(Integer, ForeignKey('entity.entity_id', ondelete="CASCADE"), nullable=False)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    comments_entity = relationship("Comments", back_populates="post", cascade="all, delete-orphan")
    user_post_info = relationship("UserPostInfo", back_populates="post", cascade="all, delete-orphan", uselist=False)
    playlist_item = relationship("PlaylistItem", back_populates="post", cascade="all, delete-orphan")
    implicit_data = relationship("ImplicitData", back_populates="post", cascade="all, delete-orphan")
    entity = relationship("Entity", back_populates="post")
    calculated_rating = relationship("CalculatedRating", back_populates="post", cascade="all, delete-orphan")



class Comments(Base):
    __tablename__ = 'comments'

    comment_id = Column(Integer, primary_key=True, name="comment_id", autoincrement=True)
    post_id = Column(Integer, ForeignKey('post.post_id', ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey('user.user_id', ondelete="CASCADE"), nullable=False)
    comment = Column(String, nullable=False)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    post = relationship("Post", back_populates="comments_entity")
    user = relationship("User", back_populates="comments")


class UserPostInfo(Base):
    __tablename__ = 'user_post_info'

    user_id = Column(Integer, ForeignKey('user.user_id', ondelete="CASCADE"), nullable=False, primary_key=True)
    post_id = Column(Integer, ForeignKey('post.post_id', ondelete="CASCADE"), nullable=False, primary_key=True)
    liked = Column(Boolean, default=False)
    user_rating = Column(Float, default=0)
    seen = Column(Boolean, default=False)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    user = relationship("User", back_populates="user_post_info")
    post = relationship("Post", back_populates="user_post_info")


class Playlist(Base):
    __tablename__ = 'playlist'

    playlist_id = Column(Integer, primary_key=True, name="playlist_id", autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id', ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    user = relationship("User", back_populates="playlist")
    playlist_item = relationship("PlaylistItem", back_populates="playlist")
    saved_playlist = relationship("SavedPlaylist", back_populates="playlist")


class PlaylistItem(Base):
    __tablename__ = 'playlist_item'

    playlist_item_id = Column(Integer, primary_key=True, name="playlist_item_id", autoincrement=True)
    playlist_id = Column(Integer, ForeignKey('playlist.playlist_id', ondelete="CASCADE"), nullable=False)
    post_id = Column(Integer, ForeignKey('post.post_id'), nullable=False)
    order = Column(Integer, nullable=False)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    playlist = relationship("Playlist", back_populates="playlist_item")
    post = relationship("Post", back_populates="playlist_item")


class ImplicitData(Base):
    __tablename__ = 'implicit_data'

    implicit_data_id = Column(Integer, primary_key=True, name="implicit_data_id", autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id', ondelete="CASCADE"), nullable=False)
    post_id = Column(Integer, ForeignKey('post.post_id', ondelete="CASCADE"), nullable=False)
    clicked = Column(Boolean, default=False)
    miliseconds_seen = Column(BigInteger, default=0)
    comments = Column(Integer, default=0)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    user = relationship("User", back_populates="implicit_data")
    post = relationship("Post", back_populates="implicit_data")

class CalculatedRating(Base):
    __tablename__ = 'calculated_rating'

    calculated_rating_id = Column(Integer, primary_key=True, name="calculated_rating_id", autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id', ondelete="CASCADE"), nullable=False)
    post_id = Column(Integer, ForeignKey('post.post_id', ondelete="CASCADE"), nullable=False)
    rating = Column(Float, default=0)
    created_date = Column(FormattedDate, name="created_date", default=date.today())
    updated_date = Column(FormattedDate, name="updated_date", default=date.today(), onupdate=date.today())

    user = relationship("User", back_populates="calculated_rating")
    post = relationship("Post", back_populates="calculated_rating")

class SavedPlaylist(Base):
    __tablename__ = 'saved_playlist'

    saved_playlist_id = Column(Integer, primary_key=True, name="saved_playlist_id", autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id', ondelete="CASCADE"), nullable=False)
    playlist_id = Column(Integer, ForeignKey('playlist.playlist_id', ondelete="CASCADE"), nullable=False)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    user = relationship("User", back_populates="saved_playlist")
    playlist = relationship("Playlist", back_populates="saved_playlist")


class ChatHistory(Base):
    __tablename__ = 'chat_history'

    message_id = Column(Integer, primary_key=True, name="message_id", autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id', ondelete="CASCADE"), nullable=False)
    bot_made = Column(Boolean, default=False)
    order = Column(Integer, nullable=False)
    message = Column(String, nullable=False)
    chat_id = Column(Integer, nullable=False)
    created_date = Column(FormattedDateTime, default=lambda: datetime.now(ARG_TZ))

    user = relationship("User", back_populates="chat_history")

class EntityGenre(Base):
    __tablename__ = 'entity_genre'

    entity_genre_id = Column(Integer, primary_key=True, name="entity_genre_id", autoincrement=True)
    entity_id = Column(Integer, ForeignKey('entity.entity_id', ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    entity = relationship("Entity", back_populates="genres")

class EntityProductionCompany(Base):
    __tablename__ = 'entity_production_company'

    entity_production_company_id = Column(Integer, primary_key=True, name="entity_production_company_id", autoincrement=True)
    entity_id = Column(Integer, ForeignKey('entity.entity_id', ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    entity = relationship("Entity", back_populates="entity_production_companies")

class WatchProvider(Base):
    __tablename__ = 'watch_provider'

    watch_provider_id = Column(Integer, primary_key=True, name="watch_provider_id", autoincrement=True)
    provider_name = Column(String, nullable=False)
    entity_id = Column(Integer, ForeignKey('entity.entity_id', ondelete="CASCADE"), nullable=False)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    entity = relationship("Entity", back_populates="watch_providers")

class Actor(Base):
    __tablename__ = 'actor'

    actor_id = Column(Integer, primary_key=True, name="actor_id", autoincrement=True)
    name = Column(String, nullable=False)
    entity_id = Column(Integer, ForeignKey('entity.entity_id', ondelete="CASCADE"), nullable=False)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    entity = relationship("Entity", back_populates="actors")

class Entity(Base):
    __tablename__ = 'entity'

    entity_id = Column(Integer, primary_key=True, name="entity_id", autoincrement=True)
    entity_type = Column(String, nullable=False)
    tmbd_id = Column(Integer)
    imdb_id = Column(String)
    title = Column(String)
    vote_average = Column(Float)
    release_date = Column(FormattedDate)
    revenue = Column(BigInteger)
    runtime = Column(Integer)
    budget = Column(BigInteger)
    original_language = Column(String)
    overview = Column(String)
    popularity = Column(Float)
    tagline = Column(String)
    trailer = Column(String)
    director = Column(String)
    image_key = Column(String)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    post = relationship("Post", back_populates="entity")
    genres = relationship("EntityGenre", back_populates="entity")
    entity_production_companies = relationship("EntityProductionCompany", back_populates="entity")
    actors = relationship("Actor", back_populates="entity")
    watch_providers = relationship("WatchProvider", back_populates="entity")
