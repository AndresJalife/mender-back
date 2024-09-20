from fastapi import APIRouter, HTTPException, Depends
from requests import HTTPError
from starlette.responses import JSONResponse

from ..config.database import Database, get_db
from ..config.firebase import pb
from ..model import requests
from ..models import User
from ..service.Logger import logger
from firebase_admin import auth as fauth
from ..service.auth import get_current_uid

login_router = APIRouter(
    prefix="/login",
    tags=["Login"],
)


@login_router.post("",  description="Validates user and password. Returns the user logged or an exception.", response_model=requests.SigninResponse, status_code=200)
async def login(request: requests.SigninRequest,
                db: Database = Depends(get_db)):
    try:
        user = pb.auth().sign_in_with_email_and_password(request.email, request.password)
        jwt = user['idToken']
        decoded_token = fauth.verify_id_token(jwt)
        enabled = True
        try:
            enabled = db.query(User).filter(User.email == request.email).one_or_none().enabled
        except:
            pass
        customToken = fauth.create_custom_token(decoded_token['uid'], {
            'admin': decoded_token['admin'],
            'enabled': enabled,
        })
        logger.info(f'User: {request.email} logged in')
        return JSONResponse(content={
                                'token': jwt,
                                'email': request.email,
                                'name': user['displayName'],
                                'user_id': decoded_token['userId'],
                                'customToken': customToken.decode('utf-8'),
                                'admin': decoded_token['admin'],
                                'enabled': enabled,
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


@login_router.post("/password/recovery", description="Resets the password of a user. Returns an exception if the email is not found.", status_code=200)
async def reset_password(recovery_info: requests.ResetPasswordRequest):
    try:
        pb.auth().send_password_reset_email(recovery_info.email)
        logger.info(f'Reset password email sent to {recovery_info.email}')
        return JSONResponse(content={'message': 'Reset password email sent'}, status_code=200)
    except Exception as a:
        logger.error(f'Error sending reset password email: {a}')
        raise HTTPException(detail={'message': f'There was an error sending the reset password email. {a}'}, status_code=400)


@login_router.put("/password", description="Changes the password of a user. Returns an exception if the email is not found.", status_code=200)
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