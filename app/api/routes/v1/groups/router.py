"""
Groups router module. Contains all routes that interact with user groups.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.default_response_models import DefaultResponse
from app.api.routes.v1.groups.views import add_group_view, remove_group_view, change_group_name_view, \
    add_user_to_group_view, remove_user_from_group_view
from app.api.routes.v1.users.models import GroupRequestModel, GroupChangeRequestModel, \
    AddUserToGroupRequestModel
from app.api.routes.v1.utils.auth import get_admin_by_token
from app.database import DatabaseManagerAsync

router = APIRouter(prefix="/groups")


@router.post("/", response_model=DefaultResponse, dependencies=[Depends(get_admin_by_token)])
async def add_group(
        group_model: GroupRequestModel,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
) -> DefaultResponse:
    """
    Creates new group with name passed via **group_model: GroupRequestModel**. If group already exists, it throws
    409_CONFLICT exception.

    :param group_model: Group adding request model. Check GroupRequestModel class.
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with status
    """
    return await add_group_view(group_model=group_model, session=session)


@router.delete("/", response_model=DefaultResponse, dependencies=[Depends(get_admin_by_token)])
async def remove_group(
        group_model: GroupRequestModel,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
) -> DefaultResponse:
    """
    Deletes group with name passed via **group_model: GroupRequestModel**. If group not found by name, it throws
    409_CONFLICT exception.

    :param group_model: Group deletion request model. Check GroupRequestModel class.
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with status.
    """
    return await remove_group_view(group_model=group_model, session=session)


@router.patch("/", response_model=DefaultResponse, dependencies=[Depends(get_admin_by_token)])
async def change_group_name(
        group_model: GroupChangeRequestModel,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
) -> DefaultResponse:
    """
    Changes existing group name. If group not found by name, it throws
    409_CONFLICT exception

    :param group_model: Group updating request model. Contains old name and a new name. Check GroupChangeRequestModel.
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with status
    """
    return await change_group_name_view(group_model=group_model, session=session)


@router.post("/add_user_to_group", response_model=DefaultResponse, dependencies=[Depends(get_admin_by_token)])
async def add_user_to_group(
        group_model: AddUserToGroupRequestModel,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
) -> DefaultResponse:
    """
    Adds user to a group. If group does not exist, then creates a new one. If user already exists, it throws
    409_CONFLICT exception

    :param group_model: User to group adding request model. Contains group name and user id.
        Check AddUserToGroupRequestModel
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with status.
    """
    return await add_user_to_group_view(group_model=group_model, session=session)


@router.post("/remove_user_from_group", response_model=DefaultResponse, dependencies=[Depends(get_admin_by_token)])
async def remove_user_from_group(
        group_model: AddUserToGroupRequestModel,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
) -> DefaultResponse:
    """
    Method removes user from group. If user not in group, it throws
    409_CONFLICT exception.

    :param group_model: Model with information about user (id) and group (name).
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with status.
    """
    return await remove_user_from_group_view(group_model=group_model, session=session)
