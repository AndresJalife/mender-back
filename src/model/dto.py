from typing import Optional

from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    admin: Optional[bool] = None
    enabled: Optional[bool] = None
    created_date: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)