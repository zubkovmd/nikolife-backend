import uuid
from datetime import timedelta
from io import BytesIO
from typing import Optional

import requests
import sqlalchemy
from fastapi import Response, Depends, HTTPException, Form, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from starlette import status

from app.api.routes.default_responses import DefaultResponse, UserRequestResponse, User, UserGoogleAuthResponse
from app.api.routes.v1.users.groups.utils import get_group_model_or_create_if_not_exists
from app.api.routes.v1.users.utility_classes import RegisterRequestModel, UserFromDB
from app.api.routes.v1.users.utils import get_user_by_id
from app.api.routes.v1.users.views.utils import get_user_model
from app.api.routes.v1.utils.auth import get_user_by_token, get_password_hash, create_access_token
from app.constants import DEFAULT_USER_GROUP_NAME, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import DatabaseManagerAsync
from app.database.models.base import Users
from app.utils.s3_service import manager as s3_manager


async def get_user_by_id_view(
        user_id: int,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)):
    async with session.begin():
        user: Users = await get_user_by_id(user_id=user_id, session=session)
        print(f"/by_id image: {user.image}")
        dicted = user.__dict__
        if user.image:
            dicted["image"] = s3_manager.get_url(user.image)
        return UserRequestResponse(detail="Пользователь найден", user=User(**dicted))


async def get_or_create_google_user_view(
        token: str,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
) -> UserGoogleAuthResponse:
    class GoogleResponseModel(BaseModel):
        id: str
        email: str
        name: str
        picture: Optional[str]

    headers = {"Authorization": f"Bearer {token}"}
    url = "https://www.googleapis.com/oauth2/v1/userinfo"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json()["message"])
    response = response.json()
    valideted_google_user = GoogleResponseModel(**response)
    async with session.begin():
        stmt = sqlalchemy.select(Users).filter(Users.email == valideted_google_user.email).limit(1)
        user: Optional[Users] = (await session.execute(stmt)).scalars().first()
        if not user:
            user = Users(
                username=valideted_google_user.email,
                email=valideted_google_user.email,
                info="",
                password=uuid.uuid4().hex,
                name=valideted_google_user.name,
            )
            if valideted_google_user.picture:
                filename = f"{valideted_google_user.email}/avatar.png"
                s3_manager.send_memory_file_to_s3(file=BytesIO(requests.get(valideted_google_user.picture).content),
                                                  object_key=filename)
                user.image = filename
            user.groups.append(await get_group_model_or_create_if_not_exists(group_name=DEFAULT_USER_GROUP_NAME,
                                                                             session=session))
            session.add(user)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            username=user.username, expires_delta=access_token_expires
        )
        dicted = user.__dict__.copy()
        print(f"/google image: {dicted['image']}")
        if user.image:
            dicted["image"] = s3_manager.get_url(user.image)
        return UserGoogleAuthResponse(detail="Пользователь найден", user=User(**dicted), jwt=token)


async def register_user_view(user: RegisterRequestModel,
                             session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)):
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


async def delete_user_view(session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
                           current_user: Users = Depends(get_user_by_token)):
    user_to_delete = UserFromDB(**current_user.__dict__)
    async with session.begin():
        user: Users = await get_user_model(session=session, username=user_to_delete.username)
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
                           current_user: Users = Depends(get_user_by_token),
                           ):
    user_to_update = UserFromDB(**current_user.__dict__)
    async with session.begin():
        user: Users = await get_user_model(session=session, username=user_to_update.username)
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
            s3_manager.send_memory_file_to_s3(image.file, object_key=object_key)
            user.image = object_key
        return DefaultResponse(detail="Информация о пользователе обновлена")
