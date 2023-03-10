"""Whole application configuration. Configuration uses pydantic BaseSettings.
Check https://pydantic-docs.helpmanual.io/usage/settings/"""
import base64
from typing import Literal, Optional

from pydantic import BaseModel, BaseSettings, validator, Field


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

    @validator("host")
    def cleanup_host(cls, host):
        return host.replace("\n", "").replace("\r", "")

    @validator("username")
    def cleanup_username(cls, username):
        return username.replace("\n", "").replace("\r", "")

    @validator("password")
    def cleanup_password(cls, password):
        return password.replace("\n", "").replace("\r", "")

    @validator("name")
    def cleanup_name(cls, name):
        return name.replace("\n", "").replace("\r", "")


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
    host: str
    """s3 host"""
    port: int
    """s3 port"""

    @validator("acckey")
    def cleanup_access_key(cls, acckey):
        return acckey.replace("\n", "").replace("\r", "")

    @validator("seckey")
    def cleanup_secret_key(cls, seckey):
        return seckey.replace("\n", "").replace("\r", "")

    @validator("endpoint")
    def cleanup_endpoint(cls, endpoint):
        return endpoint.replace("\n", "").replace("\r", "")

    @validator("bucket")
    def cleanup_bucket(cls, bucket):
        return bucket.replace("\n", "").replace("\r", "")


class Sentry(BaseModel):
    """Sentry configuration model"""
    dsn: Optional[str] = None
    """sentry dsn"""

    @validator("dsn")
    def cleanup_dsn(cls, dsn):
        if dsn:
            return dsn.replace("\n", "").replace("\r", "")


class ApiSettings(BaseModel):
    """api jwt secret key"""
    secret_key: str

    @validator("secret_key")
    def cleanup_secret_key(cls, secret_key):
        return secret_key.replace("\n", "").replace("\r", "")


class AppleAuthProviderSettings(BaseModel):
    """Apple authentication settings"""
    private_key: str  # Base64 encoded key
    auth_link: str = "https://appleid.apple.com/auth/token"
    team_id: str # apple developer team id
    bundle_id: str # apple developer bundle id

    @validator("private_key")
    def decode_base64_private_key(cls, value):
        return base64.b64decode(value)


class GoogleAuthProviderSettings(BaseModel):
    """Google authentication settings"""
    auth_link: str = "https://www.googleapis.com/oauth2/v1/userinfo"


class UserAuthenticationSettings(BaseModel):
    """Settings for user authentication providers"""
    google_provider: GoogleAuthProviderSettings = GoogleAuthProviderSettings(
        auth_link="https://www.googleapis.com/oauth2/v1/userinfo"
    )
    apple_provider: AppleAuthProviderSettings


class Settings(BaseSettings):
    """Base settings class"""
    database: Database
    s3: S3Service
    sentry: Optional[Sentry]
    user_auth: UserAuthenticationSettings
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


settings = Settings()
