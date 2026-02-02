from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .models import Base


class Database:
    def __init__(self, database_url: str) -> None:
        self.engine = create_async_engine(database_url, future=True, echo=False)
        self._session_factory = sessionmaker(
            self.engine,
            expire_on_commit=False,
            class_=AsyncSession
        )

    def get_session(self) -> AsyncSession:
        return self._session_factory()

    async def init_models(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
