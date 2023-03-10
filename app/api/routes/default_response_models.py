"""
Module that contains default FastAPI response models.
Check https://fastapi.tiangolo.com/tutorial/response-model/.
"""

from typing import Optional

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


class User(BaseModel):
    """Model with user info for response"""
    username: str
    image: Optional[str]
    email: str
    name: str
    info: str


class UserRequestResponse(DefaultResponse):
    """Response with user info"""
    user: User


class UserAuthResponse(DefaultResponse):
    """Response with user info for google authentication"""
    user: User
    jwt: str
