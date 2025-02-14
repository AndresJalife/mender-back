from firebase_admin import auth
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends, Response, status, HTTPException, Request, BackgroundTasks
from src.config.database import Database, get_db
from src.service.UserService import UserService


def get_user_service(background_tasks: BackgroundTasks, db: Database = Depends(get_db)) -> UserService:
    return UserService(db, background_tasks)


def authenticate_and_get_user(req: Request, res: Response,
                              credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
                              user_service: UserService = Depends(get_user_service)):
    id_token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        user = user_service.get_user_by_uuid(uid)
    except Exception as err:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication from Firebase. {err}",
                headers={'WWW-Authenticate': 'Bearer error="invalid_token"'},
        )
    res.headers['WWW-Authenticate'] = 'Bearer realm="auth_required"'
    return user
