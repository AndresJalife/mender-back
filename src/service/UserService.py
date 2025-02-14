from firebase_admin import auth
from fastapi import HTTPException, BackgroundTasks
from firebase_admin import auth as fauth

from src.config.database import Database
from src.model import dto
from src.models import User
from src.service.Logger import logger
from src.service.PostService import PostService


class UserService:
    def __init__(self, db: Database, background_tasks: BackgroundTasks):
        self.db = db
        self.background_tasks = background_tasks
        self.post_service = PostService(db, background_tasks)

    def create_user(self, request: dto.User):
        logger.info(f"Creating user {request.email} with request: {request.dict(exclude={'password'})}")
        try:
            user = auth.create_user(
                    email=request.email,
                    password=request.password,
                    display_name=request.name
            )
            request.uid = user.uid
            user_id = self._create_db_user(request)
            auth.set_custom_user_claims(user.uid, {'userId': user_id})
            logger.info(f"User {request.email} created")
            self.background_tasks.add_task(self._create_extra_data, user_id)
        except Exception as e:
            logger.error(f"Error creating user {request.email}: {e}")
            raise HTTPException(detail={'message': f'{e}'}, status_code=400)

    def change_password(self, user, request):
        try:
            user = self.db.query(User).filter(User.uid == user.uid).one_or_none()
            if not user:
                raise HTTPException(detail={'message': f'User not found'}, status_code=400)
            if user.email != request.email:
                raise HTTPException(detail={'message': f'User wrong email'}, status_code=400)
            fauth.update_user(user.uid, password=request.password)
            logger.info(f'Password changed for user {request.email}')
            return "Password changed"
        except Exception as a:
            logger.error(f'Error changing password: {a}')
            raise HTTPException(detail={'message': f'There was an error changing the password. {a}'}, status_code=400)

    def update_user(self, user, user_id):
        logger.info(f"Updating user {user_id} with attrs {user.dict()}")
        db_user = self.db.query(User).filter(User.user_id == user_id).one()
        self._update_db_user(user, user_id)
        auth.update_user(db_user.uid, email=user.email, display_name=user.name)
        logger.info(f"User {user_id} updated")

    def _create_db_user(self, request):
        db_user = User(**request.dict())
        self.db.add(db_user)
        self.db.commit()
        return db_user.user_id

    def _update_db_user(self, user, user_id):
        self.db.query(User).filter(User.user_id == user_id).update(user.dict())
        self.db.commit()

    def delete_user(self, user_id):
        logger.info(f"Deleting user: {user_id}")
        self.db.query(User).filter(User.user_id == user_id).delete()
        self.db.commit()
        logger.info(f"Deleted user: {user_id}")

    def get_user(self, user_id):
        logger.info(f"Getting user {user_id}")
        user = self.db.query(User).filter(User.user_id == user_id).one()
        return user

    def get_user_by_uuid(self, user_uuid):
        logger.info(f"Getting user by uuid {user_uuid}")
        user = self.db.query(User).filter(User.uid == user_uuid).one()
        return user

    def _create_extra_data(self, user_id):
        logger.info(f"Creating extra data for user {user_id}")
        logger.info(f"Created extra data for user {user_id}")