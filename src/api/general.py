from fastapi import APIRouter, Depends, BackgroundTasks

from ..config.database import Database, get_db
from ..model import requests, dto
from ..service.GeneralService import GeneralService

genera_router = APIRouter(
        prefix="/general",
        tags=["General"],
)


def get_general_service(background_tasks: BackgroundTasks, db: Database = Depends(get_db)) -> GeneralService:
    return GeneralService(db, background_tasks)


@genera_router.post("/login", description="Validates user and password. Returns the user logged or an exception.",
                    response_model=requests.SigninResponse, status_code=200)
async def login(request: requests.SigninRequest,
                general_service: GeneralService = Depends(get_general_service),
                db: Database = Depends(get_db)):
    return general_service.login(request)


@genera_router.post("/signup", description="", response_model=None, status_code=201)
async def signup(request: dto.User,
                 general_service: GeneralService = Depends(get_general_service),
                 db: Database = Depends(get_db)):
    general_service.create_user(request)
