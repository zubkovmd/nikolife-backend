"""
Users router module. Contains all routes that interact with user.
"""

from typing import Union

from fastapi import Depends, UploadFile, Form, File, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.default_response_models import DefaultResponse, UserRequestResponse, User, UserGoogleAuthResponse
from app.api.routes.v1.groups.router import router as groups_router
from app.api.routes.v1.users.models import RegisterRequestModel
from app.api.routes.v1.users.views import get_user_by_id_view, register_user_view, delete_user_view, \
    update_user_view, get_or_create_google_user_view
from app.api.routes.v1.utils.auth import get_user_by_token
from app.api.routes.v1.utils.service_models import UserModel
from app.database import DatabaseManagerAsync
from app.utils import S3Manager

router = APIRouter(prefix="/users", )
router.include_router(groups_router)


@router.get("/me", response_model=UserRequestResponse)
async def get_me(current_user: UserModel = Depends(get_user_by_token)) -> UserRequestResponse:
    """
    Gets user object by token.

    :param current_user: User information object
    :return: Response with user object.
    """
    user_dict = current_user.__dict__
    if current_user.image:
        # if user has a profile image, then we should get its link from s3
        user_dict["image"] = S3Manager.get_instance().get_url(f"{current_user.image}_small.jpg")
    return UserRequestResponse(detail="Пользователь найден", user=User(**user_dict))


@router.get(
    "/by_id/{user_id}",
    response_model=Union[UserRequestResponse, DefaultResponse],
    dependencies=[Depends(get_user_by_token)]
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
    return await get_user_by_id_view(user_id=user_id, session=session)


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


@router.get("/googleUser", response_model=UserGoogleAuthResponse)
async def get_or_create_google_user(
        token: str,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
) -> UserGoogleAuthResponse:
    """
    This route is using for Google authentication. First it receives a Google token. After,
    service checks user info by this token with googleapis.com/oauth2/v1/userinfo. If this user already exists,
    service returns user object. Else first service creates user with this info and then returns user object.

    :param token: Google token.
    :param session: SQLAlchemy AsyncSession object
    :return: Response with user object
    """

    return await get_or_create_google_user_view(token=token, session=session)


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
        image=image,
        session=session,
        current_user=current_user
    )
