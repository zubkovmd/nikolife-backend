"""Whole application configuration. Configuration uses pydantic BaseSettings.
Check https://pydantic-docs.helpmanual.io/usage/settings/"""

from typing import Literal

from pydantic import BaseModel, BaseSettings


class Database(BaseModel):
    """Database configuration model"""
    host: str
    """database host"""
    port: int
    """database port"""
    username: str
    """database username"""
    password: str
    """database password"""
    name: str
    """database name"""


class S3Service(BaseModel):
    """S3 configuration module"""
    acckey: str
    """s3 access key"""
    seckey: str
    """s3 secret key"""
    endpoint: str
    """s3 endpoint"""
    bucket: str
    """s3 bucket"""


class Sentry(BaseModel):
    """Sentry configuration model"""
    dsn: str
    """sentry dsn"""


class ApiSettings(BaseModel):
    """api jwt secret key"""
    secret_key: str


class Settings(BaseSettings):
    """Base settings class"""
    database: Database
    s3: S3Service
    sentry: Sentry
    api: ApiSettings
    environment: Literal['development', 'testing', 'production']

    class Config:
        """configuration for whole settings"""
        env_nested_delimiter = '__'
        """
        environment variable delimiter
        Description: you should pass environment variables for settings with this delimiter. For example:
        you need to fill database host. So you write a host address to environment variable 
        with name DATABASE__HOST. '__' there is combine settings module Database with settings parameter Host.
        Check https://pydantic-docs.helpmanual.io/usage/settings/ for more info.
        """
        case_sensitive = False
        """
        Sets case insensitive for pydantic environment variables checker.
        """
