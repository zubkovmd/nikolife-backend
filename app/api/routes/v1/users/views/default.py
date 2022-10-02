import sqlalchemy
from fastapi import Response, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from app.api.routes.default_responses import DefaultResponse, UserRequestResponse, User
from app.api.routes.v1.users.groups.utils import get_group_model_or_create_if_not_exists
from app.api.routes.v1.users.utility_classes import RegisterRequestModel, UserFromDB
from app.api.routes.v1.users.utils import get_user_by_id
from app.api.routes.v1.users.views.utils import get_user_model
from app.api.routes.v1.utils.auth import get_current_active_user, get_password_hash
from app.constants import DEFAULT_USER_GROUP_NAME
from app.database.manager import manager
from app.database.models.base import Users
from app.utils.s3_service import manager as s3_manager


async def get_user_by_id_view(
        user_id: int,
        session: AsyncSession = Depends(manager.get_session_object)):
    async with session.begin():
        user: Users = await get_user_by_id(user_id=user_id, session=session)
        return UserRequestResponse(detail="Пользователь найден", user=User(**user.__dict__))


async def register_user_view(user: RegisterRequestModel, session: AsyncSession = Depends(manager.get_session_object)):
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


async def delete_user_view(session: AsyncSession = Depends(manager.get_session_object),
                           current_user: Users = Depends(get_current_active_user)):
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
                           session: AsyncSession = Depends(manager.get_session_object),
                           current_user: Users = Depends(get_current_active_user),
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
