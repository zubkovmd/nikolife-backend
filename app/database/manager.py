import contextlib
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine, CursorResult
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession

from app.config import Settings


class DatabaseManager:
    _host: str
    _port: int
    _user: str
    _password: str
    _dbname: str
    _engine: Optional[Engine]
    _test: int

    def __init__(self, host: str, port: int, user: str, password: str, dbname: str):
        """

        :param host: hostname (127.0.0.1/host.addr.name)
        :param port: port (1234)
        :param user: database username
        :param password: database password
        :param dbname: database name
        """
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._dbname = dbname


class DatabaseManagerSync(DatabaseManager):

    def __init__(self, host: str, port: int, user: str, password: str, dbname: str = "postgres"):
        super().__init__(host=host, port=port, user=user, password=password, dbname=dbname)
        self.create_engine()

    def create_engine(self) -> None:
        """
        Function create synchronous engine for database

        :return:
        """
        self._engine: Engine = create_engine(
            f"postgresql://{self._user}:{self._password}@{self._host}:{self._port}/{self._dbname}"
        )

    @contextlib.contextmanager
    def get_session(self) -> Session:
        """
        Context manager. Output is orm database synchronous session

        :return:
        """
        session_maker = sessionmaker(self._engine)
        with session_maker() as session:
            with session.begin():
                yield session


class DatabaseManagerAsync(DatabaseManager):

    def __init__(self, host: str, port: int, user: str, password: str, dbname: str = "postgres"):
        super().__init__(host=host, port=port, user=user, password=password, dbname=dbname)
        self.create_engine()

    def create_engine(self) -> None:
        """
        Function create asynchronous engine for database

        :return:
        """
        self._engine: AsyncEngine = create_async_engine(
            f"postgresql+asyncpg://{self._user}:{self._password}@{self._host}:{self._port}/{self._dbname}",
            pool_size=1000,
        )

    def get_engine(self):
        return self._engine

    @contextlib.asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """
        Context manager. Output is orm database asynchronous session

        :return:
        """
        async_session = sessionmaker(self._engine, class_=AsyncSession)
        async with async_session() as session:
            async with session.begin():
                yield session

    async def get_session_object(self) -> AsyncSession:
        async_session = sessionmaker(self._engine, class_=AsyncSession)
        async with async_session() as session:
            try:
                yield session
            finally:
                await session.close()


manager = DatabaseManagerAsync(
    Settings().database.host,
    Settings().database.port,
    Settings().database.username,
    Settings().database.password,
    Settings().database.name
)
