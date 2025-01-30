from src.model import dto
from ..service import auth as app_auth
from ..service.UserService import UserService

from fastapi import APIRouter, HTTPException, Depends
from starlette.responses import JSONResponse

from ..config.database import Database, get_db
from ..config.firebase import pb
from ..model import requests
from ..models import User
from ..service.Logger import logger
from firebase_admin import auth as fauth

from ..service.auth import get_current_uid

user_router = APIRouter(
        prefix="/user",
        tags=["User"],
)


def get_user_service(db: Database = Depends(get_db)) -> UserService:
    return UserService(db)


@user_router.post("", description="Creates a user",
                  response_model=None,
                  status_code=201)
async def create_user(request: dto.User,
                      user_uuid: str = Depends(app_auth.get_current_uid),
                      user_service: UserService = Depends(get_user_service)):
    user_service.create_user(request)


@user_router.get("/{user_id}", description="Gets a user by id", response_model=dto.User)
async def get_user(user_id: int,
                   user_uuid: str = Depends(app_auth.get_current_uid),
                   user_service: UserService = Depends(get_user_service)):
    return user_service.get_user(user_id)


@user_router.put("/{user_id}", description="Updates a user (admin or not). Needs to be admin", response_model=None)
async def update_user(user: dto.User,
                      admin_uuid: str = Depends(app_auth.get_current_uid),
                      user_service: UserService = Depends(get_user_service),
                      user_id: int = None):
    user_service.update_user(user, user_id)


@user_router.delete("/{user_id}", description="Deletes a client and everything related to it", response_model=None)
async def delete_user(user_id: int,
                      user_uuid: str = Depends(app_auth.get_current_uid),
                      user_service: UserService = Depends(get_user_service)):
    return user_service.delete_user(user_id)


@user_router.post("/password/recovery",
                  description="Resets the password of a user. Returns an exception if the email is not found.",
                  status_code=200)
async def reset_password(recovery_info: requests.ResetPasswordRequest):
    try:
        pb.auth().send_password_reset_email(recovery_info.email)
        logger.info(f'Reset password email sent to {recovery_info.email}')
        return JSONResponse(content={'message': 'Reset password email sent'}, status_code=200)
    except Exception as a:
        logger.error(f'Error sending reset password email: {a}')
        raise HTTPException(detail={'message': f'There was an error sending the reset password email. {a}'},
                            status_code=400)


@user_router.put("/password",
                 description="Changes the password of a user. Returns an exception if the email is not found.",
                 status_code=200)
async def change_password(request: requests.ChangePasswordRequest,
                          user_uuid: str = Depends(get_current_uid),
                          db: Database = Depends(get_db)):
    try:
        user = db.query(User).filter(User.uid == user_uuid).one_or_none()
        if not user:
            raise HTTPException(detail={'message': f'User not found'}, status_code=400)
        if user.email != request.email:
            raise HTTPException(detail={'message': f'User wrong email'}, status_code=400)
        fauth.update_user(user_uuid, password=request.password)
        logger.info(f'Password changed for user {request.email}')
        return JSONResponse(content={'message': 'Password changed'}, status_code=200)
    except Exception as a:
        logger.error(f'Error changing password: {a}')
        raise HTTPException(detail={'message': f'There was an error changing the password. {a}'}, status_code=400)
