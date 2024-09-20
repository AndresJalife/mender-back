from typing import Optional

from pydantic import BaseModel, ConfigDict
from ..enums.UserTypes import UserTypes

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str
    type: UserTypes
    prod: bool
    model_config = ConfigDict(from_attributes=True,
                              json_schema_extra=
                                {"example": {
                                    'email': 'andyjalife@gmail.com',
                                    'password': 'password',
                                    'name': 'Andy',
                                    'type': 'admin/client',
                                    'prod': True,
                                    'views': ['monotribute', 'planification', 'debt', 'documents']
                                }})

class SigninRequest(BaseModel):
    email: str
    password: str
    model_config = ConfigDict(from_attributes=True)


class SigninResponse(BaseModel):
    token: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    user_id: Optional[int] = None
    customToken: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ResetPasswordRequest(BaseModel):
    email: str
    model_config = ConfigDict(from_attributes=True)


class ChangePasswordRequest(BaseModel):
    email: str
    password: str
    model_config = ConfigDict(from_attributes=True)
