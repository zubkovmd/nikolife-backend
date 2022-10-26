"""Utility methods for groups: Groups manipulation"""

import sqlalchemy
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.database.models.base import Groups


async def add_group(group_name: str, session: AsyncSession):
    """
    Method creates new group: Groups. If group with this name already exists, then service throws
    409_CONFLICT exception.

    :param group_name: group name to create
    :param session: SQLAlchemy session object
    :return: None
    """
    resp = await session.execute(sqlalchemy.select(Groups).where(Groups.name == group_name).limit(1))
    group_exists = resp.scalars().first()
    if group_exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Группа {group_name} уже существует")
    else:
        new_group = Groups(name=group_name)
        session.add(new_group)


async def remove_group(group_name: str, session: AsyncSession):
    """
    Method deltes group: Groups with **group_name** from database. If group with this name is not exists, then service throws
    409_CONFLICT exception.

    :param group_name: group name to delete
    :param session: SQLAlchemy session object
    :return: None
    """
    resp = await session.execute(sqlalchemy.select(Groups).where(Groups.name == group_name).limit(1))
    group = resp.scalars().first()
    if not group:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Группа {group_name} не существует")
    else:
        await session.delete(group)


async def change_group_name(old_group_name: str, new_group_name: str, session: AsyncSession) -> None:
    """
    Method changes existing group: Groups name. If group with this name is not exists, then service throws
    409_CONFLICT exception.

    :param old_group_name: old group name
    :param new_group_name: new group name
    :param session: SQLAlchemy session object
    :return: None
    """
    resp = await session.execute(sqlalchemy.select(Groups).where(Groups.name == old_group_name).limit(1))
    group = resp.scalars().first()
    if not group:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Группа {old_group_name} не существует")
    else:
        group.name = new_group_name


async def get_group_model_or_create_if_not_exists(group_name: str, session):
    """
    Method checks user groups: Groups in database by name. If group with this name exists,
    then method returns it, else first creates.

    :param group_name: group name for search
    :param session: SQLAlchemy AsyncSession object
    :return: Groups mapped object
    """
    stmt = sqlalchemy.select(Groups).where(Groups.name == group_name)
    response = await session.execute(stmt)
    found_group = response.scalars().first()
    if found_group:
        return found_group
    else:
        session.add(found_group := Groups(name=group_name))
        return found_group
