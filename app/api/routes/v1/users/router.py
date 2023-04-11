"""
Users router module. Contains all routes that interact with user.
"""

from typing import Union

from fastapi import Depends, UploadFile, Form, File, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.default_response_models import DefaultResponse, UserRequestResponse, User, UserAuthResponse, \
    UsersRequestResponse
from app.api.routes.v1.groups.router import router as groups_router
from app.api.routes.v1.users.models import RegisterRequestModel
from app.api.routes.v1.users.views import register_user_view, delete_user_view, \
    update_user_view, authenticate_by_provider_view, get_all_users_view, get_user_by_id_view
from app.api.routes.v1.utils.auth import get_user_by_token, get_admin_by_token
from app.api.routes.v1.utils.service_models import UserModel
from app.database import DatabaseManagerAsync
from app.database.models.base import Users
from app.utils import S3Manager
from app.utils.auth import AvailableAuthProviders

router = APIRouter(prefix="/users", )
router.include_router(groups_router)


@router.get("/me", response_model=UserRequestResponse)
async def get_me(
        current_user: UserModel = Depends(get_user_by_token),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
) -> UserRequestResponse:
    """
    Gets user object by token.

    :param session: FastAPI dependency, SQLAlchemy session object.
    :param current_user: User information object
    :return: Response with user object.
    """
    user_dict = current_user.__dict__
    if current_user.image:
        # if user has a profile image, then we should get its link from s3
        user_dict["image"] = S3Manager.get_instance().get_url(f"{current_user.image}_small.jpg")
    user_dict["groups"] = await Users.get_groups_with_expiration_time(user_id=current_user.id, session=session)
    return UserRequestResponse(detail="Пользователь найден", user=User(**user_dict))


@router.get("/get_all", response_model=UsersRequestResponse, dependencies=[Depends(get_admin_by_token)])
async def get_all_users(
    session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
) -> UsersRequestResponse:
    """
    Returns all users

    :return: Response with user object.
    """
    users = await get_all_users_view(
        session=session
    )
    return users


@router.get(
    "/by_id/{user_id}",
    response_model=Union[UserRequestResponse, DefaultResponse],
)
async def get_user_by_id(
        user_id: int,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
) -> UserRequestResponse:
    """
    Gets user object by user id.

    :param user_id: id of user.
    :param session: FastAPI dependency, SQLAlchemy session object.
    :return: Response with user object
    """
    user = await get_user_by_id_view(user_id=user_id, session=session)
    return user


@router.post("/", response_model=DefaultResponse)
async def register_user(
        user: RegisterRequestModel,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
) -> DefaultResponse:
    """
    Register a new user.

    :param user: User object.
    :param session: FastAPI dependency, SQLAlchemy session object.
    :return: Response with status.
    """
    return await register_user_view(user=user, session=session)


@router.get("/authenticate_by_provider", response_model=UserAuthResponse)
async def authenticate_by_provider(
        token: str,
        provider: AvailableAuthProviders,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
) -> UserAuthResponse:
    """
    This route is using for apple authentication. First it receives a Google token. After,
    service checks user info by this token with googleapis.com/oauth2/v1/userinfo. If this user already exists,
    service returns user object. Else first service creates user with this info and then returns user object.

    :param token: Google token.
    :param provider: Authentication provider type
    :param session: SQLAlchemy AsyncSession object
    :return: Response with user object
    """

    return await authenticate_by_provider_view(token=token, provider=provider, session=session)


@router.delete("/", response_model=DefaultResponse)
async def delete_user(session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
                      current_user: UserModel = Depends(get_user_by_token)):
    """
    Delete a user by token. With this route authenticated user with token can delete account.

    :param session: SQLAlchemy AsyncSession object.
    :param current_user: User information object
    :return: Response with status.
    """
    return await delete_user_view(session=session, current_user=current_user)


@router.patch("/", response_model=DefaultResponse)
async def update_user(username=Form(default=None),
                      email=Form(default=None),
                      name=Form(default=None),
                      info=Form(default=None),
                      groups=Form(default=None),
                      image: UploadFile = File(default=None),
                      session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
                      current_user: UserModel = Depends(get_user_by_token),
                      ):
    """
    Update user information

    :param username: new username (optional).
    :param email: new email (optional).
    :param name: new name (optional).
    :param info: new info (optional).
    :param groups: new user groups (optional).
    :param image: new image (optional).
    :param session: SQLAlchemy AsyncSession object.
    :param current_user: User information object.
    :return: Response with status.
    """
    return await update_user_view(
        username=username,
        email=email,
        name=name,
        info=info,
        groups=groups,
        image=image,
        session=session,
        current_user=current_user
    )
