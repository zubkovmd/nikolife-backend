import sqlalchemy
from fastapi import HTTPException
from sqlalchemy.orm import selectinload
from starlette import status

from app.database.models.base import Users


async def get_user_model(session, username):
    stmt = (sqlalchemy.select(Users).where(Users.username == username).limit(1).options(selectinload("*")))
    response = await session.execute(stmt)
    user: Users = response.scalars().one()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user

