import sqlalchemy
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.routes.default_response_models import DefaultResponse
from app.api.routes.v1.users.groups.utils import add_group_if_not_exists, remove_group_if_exists, \
    change_group_name_if_exists, get_group_model_or_create_if_not_exists
from app.api.routes.v1.users.utility_classes import GroupRequestModel, GroupChangeRequestModel, \
    AddUserToGroupRequestModel
from app.api.routes.v1.users.utils import get_user_by_id
from app.api.routes.v1.utils.auth import check_is_user_admin, get_user_by_token, check_user_is_in_group
from app.database import DatabaseManagerAsync
from app.database.models.base import Users, Groups


async def add_group_view(
        group_model: GroupRequestModel,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: Users = Depends(get_user_by_token)):
    async with session.begin():
        current_user = await get_user_by_id(user_id=current_user.id, session=session)
        await check_is_user_admin(user=current_user)
        await add_group_if_not_exists(group_name=group_model.group_name, session=session)
        return DefaultResponse(detail="Группа создана")


async def remove_group_view(
        group_model: GroupRequestModel,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: Users = Depends(get_user_by_token)):
    async with session.begin():
        current_user = await get_user_by_id(user_id=current_user.id, session=session)
        await check_is_user_admin(user=current_user)
        await remove_group_if_exists(group_name=group_model.group_name, session=session)
        return DefaultResponse(detail="Группа удалена")


async def change_group_name_view(
        group_model: GroupChangeRequestModel,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: Users = Depends(get_user_by_token)):
    async with session.begin():
        current_user = await get_user_by_id(user_id=current_user.id, session=session)
        await check_is_user_admin(user=current_user, session=session)
        await change_group_name_if_exists(
            old_group_name=group_model.old_group_name,
            new_group_name=group_model.new_group_name,
            session=session)
        return DefaultResponse(detail="Имя группы изменено")


async def add_user_to_group_view(
        group_model: AddUserToGroupRequestModel,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: Users = Depends(get_user_by_token)):
    async with session.begin():
        current_user = await get_user_by_id(user_id=current_user.id, session=session)
        await check_is_user_admin(user=current_user, session=session)
        user: Users = await get_user_by_id(user_id=group_model.user_id, session=session)

        try:
            await check_user_is_in_group(group_name=group_model.group_name, user=user, session=session)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"Пользователь уже состоит в группе {group_model.group_name}")
        except HTTPException as e:
            if e.status_code != status.HTTP_401_UNAUTHORIZED:
                raise
            user.groups.append(await get_group_model_or_create_if_not_exists(
                group_name=group_model.group_name, session=session))
            return DefaultResponse(detail="Пользователь добавлен в группу")


async def remove_user_from_group_view(
        group_model: AddUserToGroupRequestModel,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: Users = Depends(get_user_by_token)):
    async with session.begin():
        current_user = await get_user_by_id(user_id=current_user.id, session=session)
        await check_is_user_admin(user=current_user, session=session)
        user: Users = await get_user_by_id(user_id=group_model.user_id, session=session)

        try:
            await check_user_is_in_group(group_name=group_model.group_name, user=user, session=session)
            needed_group = list(filter(lambda x: x.name == group_model.group_name, user.groups))[0]
            user.groups.remove(needed_group)
            return DefaultResponse(detail=f"Пользователь удален из группы {group_model.group_name}")
        except HTTPException as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Пользователь не состоит в группе {group_model.group_name}")
