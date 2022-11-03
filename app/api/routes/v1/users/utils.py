"""Utility methods for user routes"""

from typing import Optional

import requests
import sqlalchemy
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from app.api.routes.v1.users.models import GoogleResponseModel
from app.database.models.base import Users


async def get_user_by_id(user_id: int, session: AsyncSession, join_tables: Optional[list] = None) -> Users:
    """
    Method returns user object from database with search by id. If user with this id does not exists, then throws
    404_NOT_FOUND exception.

    :param user_id: user id to search.
    :param session: SQLAlchemy AsyncSession object.
    :param join_tables: what tables should be joined to user object.
    :return: User object.
    """
    stmt = (
        sqlalchemy.select(Users)
        .filter(Users.id == user_id)
        .limit(1)
    )
    if join_tables is not None:
        stmt = stmt.options(selectinload(*join_tables))
    resp = await session.execute(stmt)
    user = resp.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


async def get_user_by_username(session, username, join_tables: Optional[list] = None):
    """
    Method returns user object from database with search by id. If user with this id does not exists, then throws
    404_NOT_FOUND exception.

    :param username:  username to search.
    :param session: SQLAlchemy AsyncSession object.
    :param join_tables: what tables should be joined to user object.
    :return: User object.
    """
    stmt = (
        sqlalchemy.select(Users)
        .where(Users.username == username)
        .limit(1)
    )
    if join_tables is not None:
        stmt = stmt.options(selectinload(*join_tables))
    response = await session.execute(stmt)
    user: Users = response.scalars().one()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


async def get_google_user(google_token: str) -> GoogleResponseModel:
    """
    Method makes request to google services with google token for user info.

    :param google_token: Google api token
    :return: Google user object
    """
    headers = {"Authorization": f"Bearer {google_token}"}
    url = "https://www.googleapis.com/oauth2/v1/userinfo"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Нужно повторить вход в приложение")
    response = response.json()
    return GoogleResponseModel(**response)
