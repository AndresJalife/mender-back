from firebase_admin import auth
from sqlalchemy import not_
from starlette.responses import JSONResponse
from fastapi import HTTPException

from src.enums.UserTypes import UserTypes
from src.models import User
from src.service.Logger import logger

class UserService:
    def __init__(self, db):
        self.db = db

    def get_users(self):
        logger.info("Getting all users")
        user_list = self.db.query(User).all()
        return user_list

    def create_user(self, request):
        logger.info(f"Creating user {request.email} with request: {request.dict(exclude={'password'})}")
        try:
            user = auth.create_user(
                email=request.email,
                password=request.password,
                display_name=request.name
            )
            user_id = self._create_db_user(request, user)
            auth.set_custom_user_claims(user.uid, {'admin': request.type == UserTypes.ADMIN,
                                                   'prod': request.prod,
                                                   'userId': user_id})
            logger.info(f"User {request.email} created")
            return JSONResponse(content={'message': f'Successfully created user', 'user_id': user_id}, status_code=201)
        except Exception as e:
            logger.error(f"Error creating user {request.email}: {e}")
            raise HTTPException(detail={'message': f'{e}'}, status_code=400)

    def update_user(self, user, user_id):
        logger.info(f"Updating user {user_id} with attrs {user.dict()}")
        db_user = self.db.query(User).filter(User.user_id == user_id).one()
        self._update_db_user(user, db_user)
        auth.update_user(db_user.uid, email=user.email, display_name=user.name)
        logger.info(f"User {user_id} updated")

    def disable_user(self, user_id):
        logger.info(f"Disabling user {user_id}")
        user = self.db.query(User).filter(User.user_id == user_id).one()
        user.enabled = False
        self.db.commit()
        auth.update_user(user.uid, disabled=True)
        logger.info(f"User {user_id} disabled")

    def enable_user(self, user_id):
        logger.info(f"Enabling user {user_id}")
        user = self.db.query(User).filter(User.user_id == user_id).one()
        user.enabled = True
        self.db.commit()
        auth.update_user(user.uid, disabled=False)
        logger.info(f"User {user_id} enabled")

    def _create_db_user(self, request, user):
        db_user = User(uid=user.uid, email=request.email, name=request.name,
                       admin=request.type == UserTypes.ADMIN, prod=request.prod)
        self.db.add(db_user)
        self.db.commit()
        return db_user.user_id

    def _update_db_user(self, user, db_user):
        db_user.email = user.email
        db_user.name = user.name
        db_user.admin = user.type == UserTypes.ADMIN
        db_user.prod = user.prod
        self.db.commit()

    def delete_user(self, user_id):
        logger.info(f"Deleting user: {user_id}")
        self.db.query(User).filter(User.user_id == user_id).delete()
        self.db.commit()
        logger.info(f"Deleted user: {user_id}")
