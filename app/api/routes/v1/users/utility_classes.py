from typing import Optional

from pydantic import BaseModel


class RegisterRequestModel(BaseModel):
    username: Optional[str]
    password: str
    email: str
    name: str
    info: str = ""


class UserFromDB(BaseModel):
    username: str
    email: str
    name: str
    info: Optional[str]
    image: Optional[str]


class GroupRequestModel(BaseModel):
    group_name: str


class GroupChangeRequestModel(BaseModel):
    old_group_name: str
    new_group_name: str


class AddUserToGroupRequestModel(BaseModel):
    user_id: int
    group_name: str
