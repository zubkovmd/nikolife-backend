"""
Module contains SQLAlchemy database connection managers for sync (DatabaseManagerSync)
and async (DatabaseManagerAsync) connections.
ATTENTION: managers uses postgres databases (^11.11).
"""

import contextlib
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession

from app.config import settings


class _DatabaseManager:
    """
    Parent class for database managers. Contains connection information like host, port, etc...
    Receives this information from environment via database configuration in ./app/config.py
    """
    _host: str
    """database host address"""
    _port: int
    """database port"""
    _user: str
    """database user username"""
    _password: str
    """database user password"""
    _dbname: str
    """database name"""
    _engine: Optional[Engine]
    """database engine string"""

    def __init__(self):
        """
        Method initialize instance of _DatabaseManager. It's receives connection information from environment variables
        via ./app/config.py configuration.
        """
        host = settings.database.host
        port = settings.database.port
        user = settings.database.username
        password = settings.database.password
        dbname = settings.database.name
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._dbname = dbname


class DatabaseManagerSync(_DatabaseManager):
    """
    SQLAlchemy singleton database manager for synchronous connections
    """

    _instance = None

    def __init__(self):
        """
        Method initialize database synchronous manager
        """
        super().__init__()
        self.create_engine()

    @classmethod
    def get_instance(cls) -> 'DatabaseManagerSync':
        """
        Singleton method, returns existing DatabaseManagerSync instance, or creates it first if instance do not exist.
        :return: database manager instance
        """
        if not DatabaseManagerSync._instance:
            DatabaseManagerAsync._instance = DatabaseManagerAsync()
            return DatabaseManagerSync._instance
        else:
            return DatabaseManagerSync._instance

    def create_engine(self) -> None:
        """
        Method create synchronous engine for database and writes it to self._engine
        :return: None
        """
        self._engine: Engine = create_engine(
            f"postgresql://{self._user}:{self._password}@{self._host}:{self._port}/{self._dbname}"
        )

    @contextlib.contextmanager
    def get_session(self) -> Session:
        """
        Context manager. Output is database synchronous transaction
        :return: session object
        """
        session_maker = sessionmaker(self._engine)
        with session_maker() as session:
            with session.begin():
                yield session


class DatabaseManagerAsync(_DatabaseManager):
    """
    SQLAlchemy singleton database manager for asynchronous connections
    """
    _instance = None

    def __init__(self):
        """
        Method initialize database asynchronous manager
        """
        super().__init__()
        self.create_engine()

    @classmethod
    def get_instance(cls) -> 'DatabaseManagerAsync':
        """
        Singleton method, returns existing DatabaseManagerAsync instance, or creates it first if instance do not exist.
        :return: database manager instance
        """
        if not DatabaseManagerAsync._instance:
            DatabaseManagerAsync._instance = DatabaseManagerAsync()
            return DatabaseManagerAsync._instance
        else:
            return DatabaseManagerAsync._instance

    def create_engine(self) -> None:
        """
        Method create asynchronous engine for database and writes it to self._engine
        :return: None
        """
        self._engine: AsyncEngine = create_async_engine(
            f"postgresql+asyncpg://{self._user}:{self._password}@{self._host}:{self._port}/{self._dbname}",
            pool_size=1000,
        )

    def get_engine(self) -> AsyncEngine:
        """
        Method returns SQLAlchemy engine.
        :return: engine
        """
        return self._engine

    @contextlib.asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """
        Context manager. Output is orm database asynchronous session
        :return:
        """
        async_session = sessionmaker(self._engine, class_=AsyncSession)
        async with async_session() as session:
            try:
                async with session.begin():
                    yield session
            finally:
                await session.close()

    async def get_session_object(self) -> AsyncSession:
        """
        Method returns Sqlalchemy AsyncSession object
        :return: session object
        """
        async_session = sessionmaker(self._engine, class_=AsyncSession)
        async with async_session() as session:
            try:
                yield session
            finally:
                await session.close()
