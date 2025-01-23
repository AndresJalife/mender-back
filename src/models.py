from sqlalchemy.orm import relationship
from datetime import date, datetime
from src.config.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, UniqueConstraint, TypeDecorator, Float, BigInteger

metadata = Base.metadata

class FormattedDate(TypeDecorator):
    impl = Date

    def process_bind_param(self, value, dialect):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%d/%m/%Y').date()
            except ValueError:
                raise ValueError("Date must be in 'dd/mm/yyyy' format")
        return value

    def process_result_value(self, value, dialect):
        return value.strftime('%d/%m/%Y') if value else None


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


class Post(Base):
    __tablename__ = 'post'

    post_id = Column(Integer, primary_key=True, name="post_id", autoincrement=True)
    entity_id = Column(Integer, nullable=False)
    entity_type = Column(String, nullable=False)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    comments = relationship("Comments", back_populates="post")
    user_post_info = relationship("UserPostInfo", back_populates="post")
    playlist_item = relationship("PlaylistItem", back_populates="post")


class Comments(Base):
    __tablename__ = 'comments'

    post_id = Column(Integer, ForeignKey('post.post_id'), nullable=False, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False, primary_key=True)
    comment = Column(String, nullable=False)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    post = relationship("Post", back_populates="comments")
    user = relationship("User", back_populates="comments")


class UserPostInfo(Base):
    __tablename__ = 'user_post_info'

    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False, primary_key=True)
    post_id = Column(Integer, ForeignKey('post.post_id'), nullable=False, primary_key=True)
    liked = Column(Boolean, default=False)
    user_rating = Column(Float, default=0)
    seen = Column(Boolean, default=False)
    calculated_rating = Column(Float, default=0)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    user = relationship("User", back_populates="user_post_info")
    post = relationship("Post", back_populates="user_post_info")


class Playlist(Base):
    __tablename__ = 'playlist'

    playlist_id = Column(Integer, primary_key=True, name="playlist_id", autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    user = relationship("User", back_populates="playlist")
    playlist_item = relationship("PlaylistItem", back_populates="playlist")
    saved_playlist = relationship("SavedPlaylist", back_populates="playlist")


class PlaylistItem(Base):
    __tablename__ = 'playlist_item'

    playlist_item_id = Column(Integer, primary_key=True, name="playlist_item_id", autoincrement=True)
    playlist_id = Column(Integer, ForeignKey('playlist.playlist_id'), nullable=False)
    post_id = Column(Integer, ForeignKey('post.post_id'), nullable=False)
    order = Column(Integer, nullable=False)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    playlist = relationship("Playlist", back_populates="playlist_item")
    post = relationship("Post", back_populates="playlist_item")


class ImplicitData(Base):
    __tablename__ = 'implicit_data'

    implicit_data_id = Column(Integer, primary_key=True, name="implicit_data_id", autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    post_id = Column(Integer, ForeignKey('post.post_id'), nullable=False)
    clicked = Column(Boolean, default=False)
    miliseconds_seen = Column(BigInteger, default=0)
    comments = Column(Integer, default=0)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    user = relationship("User", back_populates="implicit_data")
    post = relationship("Post", back_populates="implicit_data")


class SavedPlaylist(Base):
    __tablename__ = 'saved_playlist'

    saved_playlist_id = Column(Integer, primary_key=True, name="saved_playlist_id", autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    playlist_id = Column(Integer, ForeignKey('playlist.playlist_id'), nullable=False)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    user = relationship("User", back_populates="saved_playlist")
    playlist = relationship("Playlist", back_populates="saved_playlist")


class ChatHistory(Base):
    __tablename__ = 'chat_history'

    message_id = Column(Integer, primary_key=True, name="message_id", autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)
    bot_made = Column(Boolean, default=False)
    order = Column(Integer, nullable=False)
    message = Column(String, nullable=False)
    created_date = Column(FormattedDate, name="created_date", default=date.today())

    user = relationship("User", back_populates="chat_history")


# class Movie(Base):
#     __tablename__ = 'movie'
#
#     movie_id = Column(Integer, primary_key=True, name="movie_id", autoincrement=True)
#     title = Column(String, nullable=False)
#     description = Column(String)
#     year = Column(Integer)
#     rating = Column(Float)
#     created_date = Column(FormattedDate, name="created_date", default=date.today())
#
#     movie_genre = relationship("MovieGenre", back_populates="movie")
#     movie_actor = relationship("MovieActor", back_populates="movie")
