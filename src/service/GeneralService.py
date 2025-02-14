from fastapi import HTTPException
from starlette.responses import JSONResponse

from src.config.database import Database
from src.config.firebase import pb
from src.models import User
from src.service.Logger import logger
from requests import HTTPError

from firebase_admin import auth as fauth

from src.service.UserService import UserService


class GeneralService:

    def __init__(self, db: Database, background_tasks):
        self.db = db
        self.user_service = UserService(db, background_tasks)
        self.background_tasks = background_tasks

    def create_user(self, user_dto):
        try:
            user = self.user_service.create_user(User(user_dto))
            logger.info(f'User: {user_dto.email} signed up')
            return user
        except HTTPError as e:
            if "EMAIL_EXISTS" in e.strerror:
                logger.error(f'Error signing up. Email already exists')
                raise HTTPException(detail={'message': f'Email already exists'}, status_code=400)
            else:
                logger.error(f'Error signing up')
                raise HTTPException(detail={"Error Signing up."}, status_code=400)
        except Exception as e:
            logger.error(f'Error signing up')
            raise HTTPException(detail={'message': f'There was an error signing up.'}, status_code=400)

    def login(self, request):
        try:
            user = pb.auth().sign_in_with_email_and_password(request.email, request.password)
            jwt = user['idToken']
            decoded_token = fauth.verify_id_token(jwt)

            logger.info(f'User: {request.email} logged in')
            return JSONResponse(content={
                'token': jwt,
                'email': request.email,
                'name': user['displayName'],
                'user_id': decoded_token['userId'],
                'admin': decoded_token['admin'],
            },
                    status_code=200)
        except HTTPError as e:
            if "INVALID_LOGIN_CREDENTIALS" in e.strerror:
                logger.error(f'Error logging in. Bad Credentials')
                raise HTTPException(detail={'message': f'Invalid password'}, status_code=401)
            elif "USER_DISABLED" in e.strerror:
                logger.error(f'Error logging in. User Disabled')
                raise HTTPException(detail={'message': f'User Disabled'}, status_code=401)
            elif "TOO_MANY_ATTEMPTS_TRY_LATER" in e.strerror:
                logger.error(f'Error logging in. Too many attempts')
                raise HTTPException(detail={'message': f'Too many attempts. Try again later'}, status_code=401)
            else:
                logger.error(f'Error logging in')
                raise HTTPException(detail={"Error Logging in."}, status_code=400)
        except Exception as e:
            logger.error(f'Error logging in')
            raise HTTPException(detail={'message': f'There was an error logging in.'}, status_code=400)