import os
import ssl
from datetime import date, timedelta

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.config.scheduler import scheduler
from src import models
from src.api.user import user_router
from src.config.database import engine, get_db, get_context_db
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

from src.exception_handler import setup_exception_handlers
from src.service.Logger import logger
from src.service.MailService import MailService

# CERT = os.environ.get('CERT_FILE')
# if CERT is None:
#     print("No certificate file found")
#     exit(1)
# KEY = os.environ.get('KEY_FILE')
# if KEY is None:
#     print("No key file found")
#     exit(1)
# print(f"Using certificate {CERT} and key {KEY}")
# env = os.environ.get('ENVIRONMENT')

############# Initialize FastAPI ############
app = FastAPI(title="Mender", version="0.0.1")

app.include_router(user_router)

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

# if (env == "prod"):
#     app.add_middleware(HTTPSRedirectMiddleware)
#     CERT = os.environ.get('CERT_FILE')
#     if CERT is None:
#         print("No certificate file found")
#         exit(1)
#     KEY = os.environ.get('KEY_FILE')
#     if KEY is None:
#         print("No key file found")
#         exit(1)
#     print(f"Using certificate {CERT} and key {KEY}")
#     ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
#     ssl_context.load_cert_chain(CERT, keyfile=KEY)

setup_exception_handlers(app)

############# Initialize Database ############

models.Base.metadata.create_all(bind=engine, checkfirst=True)


############# Initialize Scheduler ############

@app.on_event("startup")
async def start_scheduler():
    if not scheduler.running:
        scheduler.start()


@app.on_event("shutdown")
async def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()


mail_service = MailService()
