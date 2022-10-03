from typing import Literal

from pydantic import BaseModel, BaseSettings


class Database(BaseModel):
    host: str
    port: int
    username: str
    password: str
    name: str


class S3Service(BaseModel):
    acckey: str
    seckey: str
    endpoint: str
    bucket: str


class Sentry(BaseModel):
    dsn: str


class Settings(BaseSettings):
    database: Database
    s3: S3Service
    sentry: Sentry
    environment: Literal['development', 'testing', 'production']

    class Config:
        env_nested_delimiter = '__'
        case_sensitive = False
