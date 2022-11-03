"""
Module contains service models. It's uses for mapping some SQLAlchemy models instances to python objects.
"""
import datetime
from typing import Optional

from pydantic import BaseModel


class UserModel(BaseModel):
    """Model that represents user from database for authentication methods"""
    id: int
    last_active_time: datetime.datetime
    username: str
    password: str
    email: str
    name: str
    info: str
    image: Optional[str]
    groups: list[str]
