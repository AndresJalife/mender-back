import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert

from src.config.QueryAdapter import QueryAdapter

# Environment variables

HOST = os.environ.get('POSTGRES_HOST')
PORT = os.environ.get('POSTGRES_PORT')
USER = os.environ.get('POSTGRES_USER')
PASSWORD = os.environ.get('POSTGRES_PASSWORD')
POSTGRE_SQL_URL = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/mender"

# Async SQLAlchemy engine
engine = create_async_engine(
        POSTGRE_SQL_URL,
        echo=True,
        isolation_level="AUTOCOMMIT",  # required for things like `SET pg_trgm.similarity_threshold`
)

# Async session factory
AsyncSessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
)

# Base class for models
Base = declarative_base()


class Database:
    def __init__(self, session: AsyncSession):
        self.session = session

    def query(self, model):
        return QueryAdapter(self.session, model)

    async def bulk_upsert(self, entity, data, index_items):
        stmt = insert(entity).values(data)
        upsert_stmt = stmt.on_conflict_do_update(
                index_elements=index_items,
                set_={c.name: getattr(stmt.excluded, c.name) for c in entity.__table__.columns}
        )
        await self.session.execute(upsert_stmt)
        await self.session.commit()

    async def bulk_upsert_do_nothing(self, entity, data, index_items):
        stmt = insert(entity).values(data)
        do_nothing_stmt = stmt.on_conflict_do_nothing(index_elements=index_items)
        await self.session.execute(do_nothing_stmt)
        await self.session.commit()

    async def bulk_insert(self, entity, data):
        stmt = insert(entity).values(data)
        await self.session.execute(stmt)
        await self.session.commit()


async def get_db() -> AsyncGenerator[Database, None]:
    async with AsyncSessionLocal() as session:
        yield Database(session)


async def get_db_instance():
    async for db in get_db():
        return db


@asynccontextmanager
async def get_context_db():
    async with AsyncSessionLocal() as session:
        yield Database(session)