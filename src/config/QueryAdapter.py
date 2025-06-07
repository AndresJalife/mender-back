from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class QueryAdapter:
    def __init__(self, session: AsyncSession, model):
        self.session = session
        self.model = model
        self._stmt = select(model)
        self._options = []

    def filter(self, *args):
        self._stmt = self._stmt.filter(*args)
        return self

    def join(self, target, *props, **kwargs):
        self._stmt = self._stmt.join(target, *props, **kwargs)
        return self

    def outerjoin(self, target, *props, **kwargs):
        self._stmt = self._stmt.outerjoin(target, *props, **kwargs)
        return self

    def options(self, *args):
        self._options.extend(args)
        return self

    def order_by(self, *args):
        self._stmt = self._stmt.order_by(*args)
        return self

    def limit(self, value):
        self._stmt = self._stmt.limit(value)
        return self

    def offset(self, value):
        self._stmt = self._stmt.offset(value)
        return self

    async def all(self):
        result = await self.session.execute(self._stmt.options(*self._options))
        return result.scalars().all()

    async def first(self):
        result = await self.session.execute(self._stmt.options(*self._options))
        return result.scalars().first()

    async def one(self):
        result = await self.session.execute(self._stmt.options(*self._options))
        return result.scalars().one()

    async def one_or_none(self):
        result = await self.session.execute(self._stmt.options(*self._options))
        return result.scalars().one_or_none()
