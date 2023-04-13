import datetime
import uuid
from io import BytesIO
from typing import Optional

import requests
import jwt
import sqlalchemy

from abc import ABC, abstractmethod
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from enum import Enum

from sqlalchemy.orm import selectinload

from app.api.routes.v1.groups.utils import get_group_model_or_create_if_not_exists
from app.api.routes.v1.users.models import AuthProviderResponseModel
from app.api.routes.v1.utils.auth import create_access_token
from app.config import Settings, settings
from app.constants import DEFAULT_USER_GROUP_NAME, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database.models.base import Users
from app.utils import S3Manager


class AvailableAuthProviders(Enum):
    APPLE = "apple"
    GOOGLE = "google"


class AuthBase(ABC):

    @abstractmethod
    def authenticate(self, token: str, session: AsyncSession) -> Users:
        pass

    @abstractmethod
    def get_user_by_auth_provider(self, token):
        pass

    @classmethod
    async def get_user_object_by_mail(cls, session: AsyncSession, email: str) -> Optional[Users]:
        stmt = (
            sqlalchemy.select(Users)
            .filter(Users.email == email)
            .limit(1)
            .options(selectinload(Users.groups))
        )
        user: Optional[Users] = (await session.execute(stmt)).scalars().first()
        return user

    @classmethod
    async def generate_jwt(cls, user: Users):
        access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(
            username=user.username, expires_delta=access_token_expires
        )

    @classmethod
    async def create_user(cls, session: AsyncSession, email: str, name: str) -> Users:
        user = Users(
            username=email,
            email=email,
            info="",
            password=uuid.uuid4().hex,
            name=name,
        )
        user.groups.append(await get_group_model_or_create_if_not_exists(group_name=DEFAULT_USER_GROUP_NAME,
                                                                         session=session))
        return user

    @classmethod
    def get_acess_token(self, user: Users):
        access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            username=user.username, expires_delta=access_token_expires
        )
        return token


class GoogleAuthentication(AuthBase):

    @classmethod
    def add_picture_to_user(self, user: Users, email: str, picture: str):
        filename = f"{email}/avatar"
        S3Manager.get_instance().send_image_shaped(
            image=UploadFile(file=BytesIO(requests.get(picture).content), filename=filename),
            base_filename=filename)
        user.image = filename

    def get_user_by_auth_provider(self, token):
        headers = {"Authorization": f"Bearer {token}"}
        url = settings.user_auth.google_provider.auth_link
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Нужно повторить вход в приложение")
        response = response.json()
        user_data = AuthProviderResponseModel(**response)
        return user_data

    async def authenticate(self, token: str, session: AsyncSession) -> Users:
        """
           Method makes request to google services with google token for user info.

           :param token: Google api token
           :param session: SQLAlchemy AsyncSession object
           :return: Google user object
           """
        super().authenticate(token=token, session=session)
        google_user = self.get_user_by_auth_provider(token=token)
        # Find user by email and create account if user does not exist
        user = await AuthBase.get_user_object_by_mail(session=session, email=google_user.email)
        if not user:  # No user object for passed email in database. So we need to create new one
            user = await AuthBase.create_user(session=session, email=google_user.email, name=google_user.email)
            if google_user.picture:  # if user has a Google picture, then we should add it to service
                self.add_picture_to_user(user, google_user.email, google_user.picture)
            session.add(user)
        return user


class AppleAuthentication(AuthBase):
    """apple authentication backend"""

    def get_user_by_auth_provider(self, token):
        headers = {'content-type': "application/x-www-form-urlencoded"}
        client_id, client_secret = self.get_key_and_secret()
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': token,
            'grant_type': 'authorization_code',
            'redirect_uri': ''
        }
        res = requests.post(settings.user_auth.apple_provider.auth_link, data=data, headers=headers)
        if res.status_code != 200:
            raise HTTPException(
                detail="Ошибка аутентификации с помощью Apple",
                status_code=res.status_code
            )
        response_dict = res.json()
        id_token = response_dict.get('id_token', None)
        decoded = jwt.decode(id_token, options={"verify_signature": False})
        user_data = AuthProviderResponseModel(**decoded)
        return user_data

    def get_key_and_secret(self):
        headers = {
            'kid': "B6A22HXU5W",  # settings.SOCIAL_AUTH_APPLE_KEY_ID
        }

        payload = {
            'iss': settings.user_auth.apple_provider.team_id,
            'iat': int(datetime.datetime.now().timestamp()),
            'exp': int((datetime.datetime.now() + datetime.timedelta(days=180)).timestamp()),
            'aud': 'https://appleid.apple.com',
            'sub': settings.user_auth.apple_provider.bundle_id,
        }
        client_secret = jwt.encode(
            payload,
            settings.user_auth.apple_provider.private_key,
            algorithm='ES256',
            headers=headers
        )

        return settings.user_auth.apple_provider.bundle_id, client_secret

    async def authenticate(self, token: str, session: AsyncSession) -> Users:
        """
        Apple authentication
        """
        apple_user = self.get_user_by_auth_provider(token=token)
        # Find user by email and create account if user does not exist
        user = await AuthBase.get_user_object_by_mail(session=session, email=apple_user.email)
        if not user:  # No user object for passed email in database. So we need to create new one
            user = await AuthBase.create_user(session=session, email=apple_user.email, name=apple_user.email)
            # add default 'user' group to new user groups
            session.add(user)
        return user
