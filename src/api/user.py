from typing import List

from fastapi import APIRouter, Depends, BackgroundTasks
from src.model import dto
from ..config.database import get_db, Database
from ..service import auth as app_auth
from ..service.UserService import UserService

user_router = APIRouter(
    prefix="/user",
    tags=["User"],
)


def get_user_service(db: Database = Depends(get_db)) -> UserService:
    return UserService(db)


# @user_router.post("", description="Creates a user. Needs to be admin",
#                   response_model=requests.CreatedUserResponse,
#                   status_code=201)
# async def create_user(request: requests.SignupRequest,
#                       admin_uuid: str = Depends(app_auth.get_current_admin_uid),
#                       user_service: UserService = Depends(get_user_service)):
#     return user_service.create_user(request)


@user_router.get("", description="Get all users. Needs to be admin", response_model=List[dto.User])
async def get_all_users(admin_uuid: str = Depends(app_auth.get_current_admin_uid),
                        user_service: UserService = Depends(get_user_service)):
    return user_service.get_users()


# @user_router.put("/{user_id}", description="Updates a user (admin or not). Needs to be admin", response_model=None)
# async def update_user(user: requests.UpdateUser,
#                       admin_uuid: str = Depends(app_auth.get_current_admin_uid),
#                       user_service: UserService = Depends(get_user_service),
#                       user_id: int = None):
#     user_service.update_user(user, user_id)


@user_router.post("/{user_id}/disable", description="Disables a user. Needs to be admin", response_model=None)
async def disable_user(user_id: int,
                       admin_uuid: str = Depends(app_auth.get_current_admin_uid),
                       user_service: UserService = Depends(get_user_service)):
    user_service.disable_user(user_id)


@user_router.post("/{user_id}/enable", description="Enable a user. Needs to be admin", response_model=None)
async def enable_user(user_id: int,
                      admin_uuid: str = Depends(app_auth.get_current_admin_uid),
                      user_service: UserService = Depends(get_user_service)):
    user_service.enable_user(user_id)


@user_router.delete("/{user_id}", description="Deletes a client and everything related to it", response_model=None)
async def delete_user(user_id: int,
                      user_uuid: str = Depends(app_auth.get_current_admin_uid),
                      user_service: UserService = Depends(get_user_service)):
    return user_service.delete_user(user_id)

@user_router.post("/{user_id}/hide", description="Hides a client", response_model=None)
async def delete_user(user_id: int,
                      user_uuid: str = Depends(app_auth.get_current_admin_uid),
                      user_service: UserService = Depends(get_user_service)):
    return user_service.hide_user(user_id)