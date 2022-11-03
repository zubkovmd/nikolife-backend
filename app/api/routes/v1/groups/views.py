"""Views for user groups router"""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.routes.default_response_models import DefaultResponse
from app.api.routes.v1.groups.utils import (
    add_group,
    remove_group,
    change_group_name,
    get_group_model_or_create_if_not_exists)
from app.api.routes.v1.users.models import GroupRequestModel, GroupChangeRequestModel, \
    AddUserToGroupRequestModel
from app.api.routes.v1.users.utils import get_user_by_id
from app.api.routes.v1.utils.auth import check_user_is_in_group
from app.database.models.base import Users


async def add_group_view(
        group_model: GroupRequestModel,
        session: AsyncSession
) -> DefaultResponse:
    """
    View for new group creation.

    :param group_model: Group adding request model. Check GroupRequestModel class.
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with status
    """
    async with session.begin():
        await add_group(group_name=group_model.group_name, session=session)
        return DefaultResponse(detail="Группа создана")


async def remove_group_view(
        group_model: GroupRequestModel,
        session: AsyncSession
) -> DefaultResponse:
    """
    View for group deletion.

    :param group_model: Group deletion request model. Check GroupRequestModel class.
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with status
    """
    async with session.begin():
        await remove_group(group_name=group_model.group_name, session=session)
        return DefaultResponse(detail="Группа удалена")


async def change_group_name_view(
        group_model: GroupChangeRequestModel,
        session: AsyncSession
) -> DefaultResponse:
    """
    View for group name updating

    :param group_model: Group updating request model. Contains old name and a new name. Check GroupChangeRequestModel.
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with status
    """
    async with session.begin():
        await change_group_name(
            old_group_name=group_model.old_group_name,
            new_group_name=group_model.new_group_name,
            session=session)
        return DefaultResponse(detail="Имя группы изменено")


async def add_user_to_group_view(
        group_model: AddUserToGroupRequestModel,
        session: AsyncSession
) -> DefaultResponse:
    """
    View for user adding to group

    :param group_model: User to group adding request model. Contains group name and user id.
        Check AddUserToGroupRequestModel
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with status
    """
    async with session.begin():
        user: Users = await get_user_by_id(user_id=group_model.user_id, session=session, join_tables=[Users.groups])
        try:
            # check if user already in this group, then throws 409_CONFLICT exception.
            # this method throws 401 when user not in group
            await check_user_is_in_group(group_name=group_model.group_name, user=user)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"Пользователь уже состоит в группе {group_model.group_name}")
        except HTTPException as e:
            # now we check is exception 401 (401 means that user not in group)
            if e.status_code != status.HTTP_401_UNAUTHORIZED:
                raise
            # if user not in this group, then we request a group model from get_group_model_or_create_if_not_exists
            # and then adds user to this group
            user.groups.append(await get_group_model_or_create_if_not_exists(
                group_name=group_model.group_name, session=session))
            return DefaultResponse(detail="Пользователь добавлен в группу")


async def remove_user_from_group_view(
        group_model: AddUserToGroupRequestModel,
        session: AsyncSession
) -> DefaultResponse:
    """
    View for user deletion from group.

    :param group_model: Model with information about user (id) and group (name).
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with status.
    """
    async with session.begin():
        # first we get user with its groups from database
        user: Users = await get_user_by_id(user_id=group_model.user_id, session=session, join_tables=[Users.groups])
        # we need to check is user in this group. if not, then it throws 409
        await check_user_is_in_group(group_name=group_model.group_name, user=user)
        # now search group object and remove it from user groups
        needed_group = list(filter(lambda x: x.name == group_model.group_name, user.groups))[0]
        user.groups.remove(needed_group)
        return DefaultResponse(detail=f"Пользователь удален из группы {group_model.group_name}")
