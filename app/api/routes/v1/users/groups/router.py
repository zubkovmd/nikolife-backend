import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.routes.default_responses import DefaultResponse
from app.api.routes.v1.users.groups.views import add_group_view, remove_group_view, change_group_name_view, \
    add_user_to_group_view, remove_user_from_group_view
from app.api.routes.v1.users.utility_classes import GroupRequestModel, GroupChangeRequestModel, \
    AddUserToGroupRequestModel
from app.api.routes.v1.utils.auth import get_user_by_token
from app.database.manager import manager
from app.database.models.base import Users, Groups

router = APIRouter(prefix="/groups")


@router.post("/", response_model=DefaultResponse)
async def add_group(
        group_model: GroupRequestModel,
        session: AsyncSession = Depends(manager.get_session_object),
        current_user: Users = Depends(get_user_by_token)):
    return await add_group_view(group_model=group_model, session=session, current_user=current_user)


@router.delete("/", response_model=DefaultResponse)
async def remove_group(
        group_model: GroupRequestModel,
        session: AsyncSession = Depends(manager.get_session_object),
        current_user: Users = Depends(get_user_by_token)):
    return await remove_group_view(group_model=group_model, session=session, current_user=current_user)


@router.patch("/", response_model=DefaultResponse)
async def change_group_name(
        group_model: GroupChangeRequestModel,
        session: AsyncSession = Depends(manager.get_session_object),
        current_user: Users = Depends(get_user_by_token)):
    return await change_group_name_view(group_model=group_model, session=session, current_user=current_user)


@router.post("/add_user_to_group", response_model=DefaultResponse)
async def add_user_to_group(
        group_model: AddUserToGroupRequestModel,
        session: AsyncSession = Depends(manager.get_session_object),
        current_user: Users = Depends(get_user_by_token)):
    return await add_user_to_group_view(group_model=group_model, session=session, current_user=current_user)


@router.post("/remove_user_from_group", response_model=DefaultResponse)
async def add_user_to_group(
        group_model: AddUserToGroupRequestModel,
        session: AsyncSession = Depends(manager.get_session_object),
        current_user: Users = Depends(get_user_by_token)):
    return await remove_user_from_group_view(group_model=group_model, session=session, current_user=current_user)