from fastapi import APIRouter, HTTPException, Depends
from requests import HTTPError
from starlette.responses import JSONResponse

from ..config.database import Database, get_db
from ..config.firebase import pb
from ..model import requests, dto
from ..models import User
from ..service.GeneralService import GeneralService
from ..service.Logger import logger
from firebase_admin import auth as fauth
from ..service.auth import get_current_uid

genera_router = APIRouter(
    prefix="/general",
    tags=["General"],
)

def get_general_service(db: Database = Depends(get_db)) -> GeneralService:
    return GeneralService(db)


@genera_router.post("/login",  description="Validates user and password. Returns the user logged or an exception.", response_model=requests.SigninResponse, status_code=200)
async def login(request: requests.SigninRequest,
                general_service: GeneralService = Depends(get_general_service),
                db: Database = Depends(get_db)):
    return general_service.login(request)


@genera_router.post("/signup",  description="", response_model=None, status_code=201)
async def signup(request: dto.User,
                 general_service: GeneralService = Depends(get_general_service),
                 db: Database = Depends(get_db)):

    general_service.create_user(request)

