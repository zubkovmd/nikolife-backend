"""
Module contains all methods for user authentication
"""

from datetime import datetime, timedelta
from typing import Union, Optional

import sqlalchemy
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy.orm import joinedload
from starlette import status

from app.api.routes.v1.utils.exceptions import CredentialsException
from app.api.routes.v1.utils.service_models import UserModel
from app.config import settings
from app.constants import ADMIN_GROUP_NAME
from app.database import DatabaseManagerAsync
from app.database.models.base import Users
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = settings.api.secret_key
ALGORITHM = "HS256"


def verify_password(plain_password, hashed_password) -> True:
    """
    Checks if received password hash matches hashes password

    :param plain_password: plain password
    :param hashed_password: hashed password
    :return:
    """
    verified = pwd_context.verify(plain_password, hashed_password)
    if verified:
        return True
    else:
        raise CredentialsException()


def get_password_hash(password) -> str:
    """
    Function that returns password hash by context.

    :param password: plain password
    :return: hashed password
    """
    return pwd_context.hash(password)


class Token(BaseModel):
    """
    Token response model
    """
    access_token: str
    token_type: str


async def get_user(username: str) -> UserModel:
    """
    Function that return sqlalchemy user instance by username if user exists, else raises 404_NOT_FOUND exception.
    Also check user groups for **group_to_check** if this parameter passed. If user do not have this,
    throws unauthorized.

    :param username: username for search
    :return: User instance
    """
    async with DatabaseManagerAsync.get_instance().get_session() as session:
        stmt = (sqlalchemy.select(Users).where(Users.username == username).limit(1).options(joinedload(Users.groups)))
        response = await session.execute(stmt)
        user: Optional[Users] = response.scalars().first()
        if user:
            user_dict = user.__dict__.copy()
            user_dict["groups"] = [group.name for group in user.groups]
            user_to_return = UserModel(**user_dict)
            return user_to_return
        else:
            raise CredentialsException()


async def authenticate_user(username: str, password: str) -> UserModel:
    """
    Function that authenticates user by username and hashed password.
    Raises **CredentialsException** if credentials is not valid.

    :param username: username
    :param password: password
    :return: User instance
    """
    user: UserModel = await get_user(username)
    verify_password(password, user.password)  # verify that password is match for that user
    return user


def create_access_token(username: str, expires_delta: Union[timedelta, None] = None) -> str:
    """
    Function that generates access token

    :param username: username
    :param expires_delta: expires in
    :return: encoded token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    data = {"sub": username, "exp": expire}
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_user_by_token(
        token: str = Depends(OAuth2PasswordBearer(tokenUrl="token")),
) -> UserModel:
    """
    Function for FastAPI dependency that receives bearer token with request headers and returns user if token is valid.
    Also checks required group in user groups. Default group to check is **DEFAULT_USER_GROUP_NAME**

    :param token: Request header bearer token that will be received via FastAPI dependency.
    :return: User instance
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise CredentialsException()
    except JWTError:
        raise CredentialsException()
    user_to_return = await get_user(username=username)
    return user_to_return


async def get_admin_by_token(user: Users = Depends(get_user_by_token)) -> UserModel:
    """
    Function for FastAPI dependency. Copied **get_user_by_token** function, but checks if user is admin

    :param user: FastAPI dependency, receives user model.
    :return: User instance.
    """
    if user.groups and 'admin' in user.groups:
        return user
    else:
        raise CredentialsException()


async def check_user_is_in_group(group_name: str, user: Users) -> True:
    """
    Function that checks is **group_name** in **user.groups**

    :param group_name: Group name for check
    :param user: User instance.
    :return: True if user in group else 401_UNAUTHORIZED exception.
    """
    user_groups = user.groups
    if group_name not in [i.name for i in user_groups]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Вы не состоите в группе пользователей {group_name}")
    return True


async def check_is_user_admin(user: Users):
    """
    Function that checks is user admin

    :param user: User instance
    :return: True if user is admin else 401_UNAUTHORIZED exception.
    """
    await check_user_is_in_group(group_name=ADMIN_GROUP_NAME, user=user)
    return True
