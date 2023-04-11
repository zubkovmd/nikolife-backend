"""
Module that contains default FastAPI response models.
Check https://fastapi.tiangolo.com/tutorial/response-model/.
"""
import datetime
from typing import Optional, List

from pydantic import BaseModel


class DefaultResponse(BaseModel):
    """Default api response"""
    detail: str
    """response comment"""


class ErrorResponse(DefaultResponse):
    """Error response"""
    pass


class DefaultResponseWithPayload(DefaultResponse):
    """Default api response with some payload"""
    payload: dict
    """Payload for response"""


class GroupWithExpirationTime(BaseModel):
    """Group with expiration time model"""
    name: str
    expiration_time: Optional[datetime.datetime]


class User(BaseModel):
    """Model with user info for response"""
    username: str
    image: Optional[str]
    email: str
    name: str
    info: str
    groups: Optional[List[GroupWithExpirationTime]]
    id: Optional[int]


class UserRequestResponse(DefaultResponse):
    """Response with user info"""
    user: User


class UsersRequestResponse(DefaultResponse):
    """Response with user info"""
    users: List[User]


class UserAuthResponse(DefaultResponse):
    """Response with user info for google authentication"""
    user: User
    jwt: str
