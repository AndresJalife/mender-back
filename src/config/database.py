import os
from contextlib import contextmanager

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

HOST = os.environ.get('POSTGRES_HOST')
PORT = os.environ.get('POSTGRES_PORT')
USER = os.environ.get('POSTGRES_USER')
PASSWORD = os.environ.get('POSTGRES_PASSWORD')
POSTGRE_SQL_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/mender"

engine = create_engine(POSTGRE_SQL_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Database(Session):
    def bulk_upsert_do_nothing(self, entity, data, index_items):
        stmt = insert(entity).values(data)
        do_nothing_stmt = stmt.on_conflict_do_nothing(index_elements=index_items)
        self.execute(do_nothing_stmt)
        self.commit()

    def bulk_upsert(self, entity, data, index_items):
        stmt = insert(entity).values(data)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=index_items,
            set_={c.name: getattr(stmt.excluded, c.name) for c in entity.__table__.columns}
        )
        self.execute(upsert_stmt)
        self.commit()

    def bulk_upsert_without_conflict(self, entity, data):
        stmt = insert(entity).values(data)
        self.execute(stmt)
        self.commit()

ExtendedSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Database
)

def get_db():
    db = ExtendedSessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_context_db():
    db = ExtendedSessionLocal()
    try:
        yield db
    finally:
        db.close()
