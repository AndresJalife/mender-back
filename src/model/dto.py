from typing import Optional

from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    lastname: Optional[str] = None
    username: Optional[str] = None
    country: Optional[str] = None
    new: Optional[bool] = None
    sex: Optional[str] = None
    created_date: Optional[str] = None
    uid = Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
