"""
Module contains service models. It's uses for mapping some SQLAlchemy models instances to python objects.
"""
import datetime
from typing import Optional

from pydantic import BaseModel

from app.log import default_logger


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

    def log_debug(self, message):
        default_logger.debug(f"USER_LOG[{self.username}, {self.id}] - {message}")

    def log_info(self, message):
        default_logger.info(f"USER_LOG[{self.username}, {self.id}] - {message}")

    def log_warning(self, message):
        default_logger.warning(f"USER_LOG[{self.username}, {self.id}] - {message}")

    def log_error(self, message):
        default_logger.error(f"USER_LOG[{self.username}, {self.id}] - {message}")

    def log_exception(self, message):
        default_logger.exception(f"USER_LOG[{self.username}, {self.id}] - {message}")
