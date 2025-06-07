import time

from fastapi import FastAPI,Request
from sqlalchemy import text
from starlette.middleware.cors import CORSMiddleware

from src.config.scheduler import scheduler
from src import models
from src.api.user import user_router
from src.api.general import genera_router
from src.api.post import post_router
from src.api.chat import chat_router
from src.api.playlist import playlist_router
from src.config.database import engine, get_db, get_context_db

from src.exception_handler import setup_exception_handlers
from src.service.Logger import logger
from src.service.MailService import MailService

############# Initialize FastAPI ############
app = FastAPI(title="Mender", version="0.0.1")

app.include_router(user_router)
app.include_router(genera_router)
app.include_router(post_router)
app.include_router(chat_router)
app.include_router(playlist_router)

origins = [
    "http://localhost",
    "http://localhost:8443",
    "http://127.0.0.1:8443",
    "http://127.0.0.1"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_exception_handlers(app)

# Configure logging
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = (time.perf_counter() - start) * 1000
    logger.info(f"⏱️ Request: {request.method} {request.url.path} took {duration:.2f} ms")
    return response


############# Initialize Database ############

models.Base.metadata.create_all(bind=engine, checkfirst=True)


############# Initialize Scheduler ############

@app.on_event("startup")
async def start_scheduler():
    if not scheduler.running:
        scheduler.start()

SIM_LIMIT = 0.3

@app.on_event("startup")
async def startup():
    with engine.begin() as conn:
        conn.execute(text(f"SET pg_trgm.similarity_threshold = {SIM_LIMIT}"))


@app.on_event("shutdown")
async def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()


mail_service = MailService()