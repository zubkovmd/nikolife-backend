import sqlalchemy
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.database.models.base import Groups


async def add_group_if_not_exists(group_name: str, session: AsyncSession):
    resp = await session.execute(sqlalchemy.select(Groups).where(Groups.name == group_name).limit(1))
    group_exists = resp.scalars().first()
    if group_exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Группа {group_name} уже существует")
    else:
        new_group = Groups(name=group_name)
        session.add(new_group)


async def remove_group_if_exists(group_name: str, session: AsyncSession):
    resp = await session.execute(sqlalchemy.select(Groups).where(Groups.name == group_name).limit(1))
    group = resp.scalars().first()
    if not group:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Группа {group_name} не существует")
    else:
        await session.delete(group)


async def change_group_name_if_exists(old_group_name: str, new_group_name: str, session: AsyncSession):
    resp = await session.execute(sqlalchemy.select(Groups).where(Groups.name == old_group_name).limit(1))
    group = resp.scalars().first()
    if not group:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Группа {old_group_name} не существует")
    else:
        group.name = new_group_name


async def get_group_model_or_create_if_not_exists(group_name: str, session):
    stmt = sqlalchemy.select(Groups).where(Groups.name == group_name)
    response = await session.execute(stmt)
    found_group = response.scalars().first()
    if found_group:
        return found_group
    else:
        found_group = Groups(name=group_name)
        session.add(found_group)
        return found_group
