from typing import List

import sqlalchemy
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database.models.base import Users


async def get_user_by_id(user_id: int, session: AsyncSession, join_tables: List[str] = None) -> Users:
    stmt = sqlalchemy.select(Users).filter(Users.id == user_id).options(joinedload(join_tables if join_tables is not None else '*')).limit(1)
    resp = await session.execute(stmt)
    user = resp.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user
