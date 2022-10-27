"""Exceptions that can occurs in utils"""

from fastapi import HTTPException
from starlette import status


class CredentialsException(HTTPException):
    """
    Exception that occurs when user credentials is not valid
    """

    def __init__(self):
        """Exception initializer"""
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
