"""Module contains user models that service uses"""

from typing import Optional

from pydantic import BaseModel


class AuthProviderResponseModel(BaseModel):
    """utility model for response data from google api"""
    email: str
    picture: Optional[str]


class RegisterRequestModel(BaseModel):
    """request model for new user register"""
    username: Optional[str]
    password: str
    email: str
    name: str
    info: str = ""


class GroupRequestModel(BaseModel):
    """request model for new group register/deletion"""
    group_name: str


class GroupChangeRequestModel(BaseModel):
    """request model for group name change"""
    old_group_name: str
    new_group_name: str


class AddUserToGroupRequestModel(BaseModel):
    """request model for user adding to group"""
    user_id: int
    group_name: str
