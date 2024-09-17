
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.config.database import POSTGRE_SQL_URL

jobstores = {
    'default': SQLAlchemyJobStore(url=POSTGRE_SQL_URL)  # Use an appropriate database URL
}

scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="America/Argentina/Buenos_Aires", misfire_grace_time=10000)
