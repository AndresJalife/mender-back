from firebase_admin import auth
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends, Response, status, HTTPException, Request
import src.util.validator as validator


def get_current_uid(req: Request, res: Response, credentials: HTTPAuthorizationCredentials=Depends(HTTPBearer())):
    id_token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        validator.validate_user_active(uid)
        # validator.validate_user_views(decoded_token['views'], req.url.path, decoded_token)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication from Firebase. {err}",
            headers={'WWW-Authenticate': 'Bearer error="invalid_token"'},
        )
    res.headers['WWW-Authenticate'] = 'Bearer realm="auth_required"'
    return uid


def get_current_admin_uid(res: Response, credentials: HTTPAuthorizationCredentials=Depends(HTTPBearer())):
    id_token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(id_token)
        validator.validate_user_admin(decoded_token)
        uid = decoded_token['uid']
        validator.validate_user_active(uid)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication from Firebase. {err}",
            headers={'WWW-Authenticate': 'Bearer error="invalid_token"'},
        )
    res.headers['WWW-Authenticate'] = 'Bearer realm="auth_required"'
    return uid
