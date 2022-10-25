from typing import Optional

from pydantic import BaseModel


#  DEFAULT RESPONSES
class DefaultResponse(BaseModel):
    detail: str


class ErrorResponse(DefaultResponse):
    pass


class DefaultResponseWithPayload(DefaultResponse):
    payload: dict


class User(BaseModel):
    username: str
    image: Optional[str]
    email: str
    name: str
    info: str


class UserRequestResponse(DefaultResponse):
    user: User


class UserGoogleAuthResponse(DefaultResponse):
    user: User
    jwt: str
