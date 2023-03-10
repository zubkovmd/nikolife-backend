"""
Views for user routes
"""

import uuid
from datetime import timedelta
from io import BytesIO
from typing import Optional

import requests
import sqlalchemy
from fastapi import Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.routes.default_response_models import DefaultResponse, UserRequestResponse, User, UserAuthResponse
from app.api.routes.v1.groups.utils import get_group_model_or_create_if_not_exists
from app.api.routes.v1.users.models import RegisterRequestModel
from app.api.routes.v1.users.utils import get_user_by_id, get_user_by_username
from app.api.routes.v1.utils.auth import get_user_by_token, get_password_hash
from app.api.routes.v1.utils.service_models import UserModel
from app.api.routes.v1.utils.utility import get_raw_filename
from app.constants import DEFAULT_USER_GROUP_NAME
from app.database import DatabaseManagerAsync
from app.database.models.base import Users
from app.utils import S3Manager
from app.utils.auth import AvailableAuthProviders, AppleAuthentication, GoogleAuthentication, AuthBase


async def get_user_by_id_view(
        user_id: int,
        session: AsyncSession
) -> UserRequestResponse:
    """
    View for get user by id route (GET .../users/by_id/{user_id})

    :param user_id: user id.
    :param session: SQLAlchemy session object.
    :return: Response with user object
    """
    async with session.begin():
        user: Users = await get_user_by_id(user_id=user_id, session=session)
        dicted = user.__dict__
        if user.image:
            # if user has a profile image, then we should get its link from s3
            dicted["image"] = S3Manager.get_instance().get_url(f"{user.image}_small.jpg")
        return UserRequestResponse(detail="Пользователь найден", user=User(**dicted))


async def authenticate_by_provider_view(
        token: str,
        provider: AvailableAuthProviders,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
) -> UserAuthResponse:
    """
    View gets user object by passed token with selected auth provider

    :param token: Authentication token
    :param provider: Authentication provider type
    :param session: SQLAlchemy AsyncSession object
    :return: user object
    """

    async with session.begin():
        if provider == AvailableAuthProviders.APPLE:
            user = await AppleAuthentication().authenticate(token=token, session=session)
        elif provider == AvailableAuthProviders.GOOGLE:
            user = await GoogleAuthentication().authenticate(token=token, session=session)
        else:
            raise HTTPException(
                detail=f"Не найден провайдер {provider} для аутентификации",
                status_code=404,
            )
        dicted = user.__dict__.copy()
        if user.image:
            dicted["image"] = S3Manager.get_instance().get_url(f"{user.image}_small.jpg")
        return UserAuthResponse(detail="Пользователь найден", user=User(**dicted), jwt=await AuthBase.generate_jwt(user=user))


async def register_user_view(
        user: RegisterRequestModel,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
) -> DefaultResponse:
    """
    View for register a new user route (POST .../users/)
    :param user:
    :param session:
    :return:
    """
    async with session.begin():
        stmt = sqlalchemy.select(Users).where(Users.username == user.username)
        resp = await session.execute(stmt)
        found_user = resp.fetchall()
        if found_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Пользователь с таким ником уже зарегистрирован")
        user.password = get_password_hash(user.password)
        user.username = user.email
        new_user = Users(**user.dict())
        new_user.groups.append(await get_group_model_or_create_if_not_exists(group_name=DEFAULT_USER_GROUP_NAME,
                                                                             session=session))
        session.add(new_user)
        await session.commit()
        return DefaultResponse(detail="Регистрация успешна")


async def delete_user_view(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token)
) -> DefaultResponse:
    """
    View for delete user route.

    :param session: SQLAlchemy AsyncSession object
    :param current_user: User information object
    :return: Response with status
    """
    user_to_delete = current_user
    async with session.begin():
        user: Users = await get_user_by_username(
            session=session,
            username=user_to_delete.username,
            join_tables=[Users.created_recipes]
        )
        for recipe in user.created_recipes:
            await session.delete(recipe)
        await session.delete(user)
        return DefaultResponse(detail=f"Пользователь с ником '{user_to_delete.username}' удален из приложения")


async def update_user_view(username=Form(default=None),
                           email=Form(default=None),
                           name=Form(default=None),
                           info=Form(default=None),
                           image: UploadFile = File(default=None),
                           session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
                           current_user: UserModel = Depends(get_user_by_token),
                           ):
    """
    View for update user information router

    :param username: new username (optional).
    :param email: new email (optional).
    :param name: new name (optional).
    :param info: new info (optional).
    :param image: new image (optional).
    :param session: SQLAlchemy AsyncSession object.
    :param current_user: User information object.
    :return: Response with status
    """
    async with session.begin():
        user: Users = await get_user_by_username(session=session, username=current_user.username)
        if username:
            user.username = username
        if email:
            user.email = email
        if name:
            user.name = name
        if info:
            user.info = info
        if image:
            filename = f"{user.email}/avatar/{get_raw_filename(image.filename)}"
            S3Manager.get_instance().send_image_shaped(image=image, base_filename=filename)
            user.image = filename
        return DefaultResponse(detail="Информация о пользователе обновлена")
