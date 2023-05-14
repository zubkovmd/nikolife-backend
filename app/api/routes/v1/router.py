"""Root v1 API router"""
import datetime
import uuid

import fastapi
from datetime import timedelta

from fastapi import Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.default_response_models import DefaultResponse
from app.api.routes.v1.utils.auth import authenticate_user, Token, create_access_token, get_password_hash
from app.config import settings
from app.constants import ACCESS_TOKEN_EXPIRE_MINUTES
from app.api.routes.v1.users.router import router as users_router
from app.api.routes.v1.recipes.router import router as recipes_router
from app.api.routes.v1.blog.router import router as blog_router
from app.database import DatabaseManagerAsync
from app.database.models.base import Users, RecoveryLog
from app.utils.email_service import EmailService

router = fastapi.APIRouter(prefix="/v1")
router.include_router(users_router)
router.include_router(recipes_router)
router.include_router(blog_router)


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Route that authenticates user and returns web token

    :param form_data: User authentication data. Contains username and password.
    :return: Acess token object that contains **token_type** and **access_token**
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        username=user.username, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/recovery", response_model=DefaultResponse)
async def password_recovery(
        email: str = Form(...),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
):
    user = await Users.get_by_email(session=session, email=email)
    recovery = await RecoveryLog.create(key=uuid.uuid4().hex, user_id=user.id)
    session.add(recovery)
    EmailService.send_email(
        subject="Восстановление пароля от приложения Nikolife",
        body=f"Для восстановления пароля, перейдите по ссылке {settings.recovery_base_path}?token={recovery.key}",
        recipients=[user.email]
    )
    await session.commit()
    return DefaultResponse(detail="На вашу почту отправлено письмо с дальнейшими инструкциями")


@router.post("/set_new_password", response_model=DefaultResponse)
async def set_new_password(
    recovery_key: str = Form(...),
    new_password: str = Form(...),
    session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
):
    recovery = await RecoveryLog.get_by_key(key=recovery_key, session=session)
    if recovery.expire.replace(tzinfo=None) < datetime.datetime.now():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ключ восстановления просрочен"
        )
    user = await Users.get_by_id(user_id=recovery.user_id, session=session)
    user.password = get_password_hash(new_password)
    recovery.expire = datetime.datetime.now() - datetime.timedelta(days=1)
    await session.commit()
    return DefaultResponse(
        detail="Новый пароль успешно установлен"
    )
