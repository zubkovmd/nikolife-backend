from datetime import datetime, timedelta
from typing import Union, Optional

import sqlalchemy
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from app.constants import ADMIN_GROUP_NAME
from app.database.manager import manager
from app.database.models.base import Users
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


SECRET_KEY = Settings().api.secret_key
ALGORITHM = "HS256"


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_user(username: str) -> Optional[Users]:
    async with manager.get_session() as session:
        stmt = (sqlalchemy.select(Users).where(Users.username == username).limit(1))
        response = await session.execute(stmt)
        user: Optional[Users] = response.scalars().first()
        if user:
            user_to_return = user
            session.expunge(user_to_return)
            return user_to_return


async def authenticate_user(username: str, password: str) -> Optional[Users]:
    user = await get_user(username)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Users:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Users = Depends(get_current_user)) -> Users:
    return current_user


async def check_user_is_in_group(group_name: str, user: Users, session: AsyncSession):
    user_groups = user.groups
    if not group_name in [i.name for i in user_groups]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Вы не состоите в группе пользователей {group_name}")
    return True


async def check_is_user_admin(user: Users, session: AsyncSession):
    await check_user_is_in_group(group_name=ADMIN_GROUP_NAME, user=user, session=session)
    return True

