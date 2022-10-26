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

from app.api.routes.default_response_models import DefaultResponse, UserRequestResponse, User, UserGoogleAuthResponse
from app.api.routes.v1.groups.utils import get_group_model_or_create_if_not_exists
from app.api.routes.v1.users.models import GoogleResponseModel
from app.api.routes.v1.users.models import RegisterRequestModel
from app.api.routes.v1.users.utils import get_user_by_id, get_google_user, get_user_by_username
from app.api.routes.v1.utils.auth import get_user_by_token, get_password_hash, create_access_token
from app.api.routes.v1.utils.service_models import UserModel
from app.constants import DEFAULT_USER_GROUP_NAME, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import DatabaseManagerAsync
from app.database.models.base import Users
from app.utils import S3Manager


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
            dicted["image"] = S3Manager.get_instance().get_url(user.image)
        return UserRequestResponse(detail="Пользователь найден", user=User(**dicted))


async def get_or_create_google_user_view(
        token: str,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
) -> UserGoogleAuthResponse:
    """
    View for get or create google user route (GET .../users/googleUser )
    Description: This view receives google token. First, service request user data for this token
    from googleapis.com/oauth2/v1/userinfo. Then, service returns user data if user already registered,
    else first service register this user.

    :param token: Google token
    :param session: SQLAlchemy AsyncSession object
    :return: user object
    """
    google_user: GoogleResponseModel = await get_google_user(token)  # get google user info
    async with session.begin():
        # Find user by email and create account if user does not exist
        stmt = sqlalchemy.select(Users).filter(Users.email == google_user.email).limit(1)
        user: Optional[Users] = (await session.execute(stmt)).scalars().first()
        if not user:  # No user object for passed email in database. So we need to create new one
            user = Users(
                username=google_user.email,
                email=google_user.email,
                info="",
                password=uuid.uuid4().hex,
                name=google_user.name,
            )
            if google_user.picture:  # if use has a Google picture, then we should add it to service
                filename = f"{google_user.email}/avatar.png"
                S3Manager.get_instance().send_memory_file_to_s3(file=BytesIO(requests.get(google_user.picture).content),
                                                                object_key=filename)
                user.image = filename
            # add default 'user' group to new user groups
            user.groups.append(await get_group_model_or_create_if_not_exists(group_name=DEFAULT_USER_GROUP_NAME,
                                                                             session=session))
            session.add(user)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            username=user.username, expires_delta=access_token_expires
        )
        dicted = user.__dict__.copy()
        if user.image:
            dicted["image"] = S3Manager.get_instance().get_url(user.image)
        return UserGoogleAuthResponse(detail="Пользователь найден", user=User(**dicted), jwt=token)


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
        user: Users = await get_user_by_username(session=session, username=user_to_delete.username, join_tables=[Users.created_recipes])
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
            object_key = f"{user.username}/profile_photo.jpg"
            S3Manager.get_instance().send_memory_file_to_s3(image.file, object_key=object_key)
            user.image = object_key
        return DefaultResponse(detail="Информация о пользователе обновлена")
