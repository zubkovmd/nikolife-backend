from fastapi import HTTPException
from starlette import status


class CredentialsException(HTTPException):
    """
    Exception that occurs when user credentials is not valid
    """
    status_code = status.HTTP_401_UNAUTHORIZED,
    detail = "Could not validate credentials",
    headers = {"WWW-Authenticate": "Bearer"}
