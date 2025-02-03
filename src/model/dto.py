from typing import Optional

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


class Post:
    pass


class Playlist:
    pass


class PostSeen:
    pass