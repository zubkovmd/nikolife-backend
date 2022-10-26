from typing import List, Union

from fastapi import Depends, APIRouter, Query, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.default_response_models import DefaultResponse
from app.api.routes.v1.blog.utility_classes import GetStoriesResponseModel, PutStoriesResponseModel, \
    GetArticlesResponseModel
from app.api.routes.v1.blog.views.articles import put_article_view, get_articles_view
from app.api.routes.v1.blog.views.stories import get_stories_view, put_story_view
from app.api.routes.v1.recipes.utility_classes import GetRecipesResponseModel
from app.api.routes.v1.recipes.views.default import get_recipes_view
from app.api.routes.v1.utils.auth import get_user_by_token, check_is_user_admin
from app.api.routes.v1.utils.service_models import UserModel
from app.constants import MAX_ARTICLES_COUNT
from app.database import DatabaseManagerAsync
from app.database.models.base import Users

router = APIRouter(prefix="/blog")


@router.get("/stories", response_model=GetStoriesResponseModel)
async def get_stories(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token),
):
    return await get_stories_view(session)


@router.put("/stories", response_model=DefaultResponse)
async def put_story(
        # story_object: PutStoriesResponseModel,
        title: str = Form(...),
        thumbnail: UploadFile = Form(...),
        images: List[UploadFile] = Form(...),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token),
):
    return await put_story_view(current_user=current_user, session=session, title=title, thumbnail=thumbnail, images=images)


@router.get("/articles", response_model=GetArticlesResponseModel)
async def get_articles(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        articles_count: int = MAX_ARTICLES_COUNT,
) -> GetArticlesResponseModel:
    """
    Route that returns last **articles_count** articles. Defaults to **app.constants.MAX_ARTICLES_COUNT**.

    :param articles_count: Articles count
    :param session: SQLAlchemy session object (FastAPI dependency)
    :return: list of pydantic articles models
    """
    return await get_articles_view(articles_count=articles_count, session=session)


@router.put("/articles", response_model=DefaultResponse)
async def put_article(
        title: str = Form(...),
        image: UploadFile = Form(...),
        subtitle: str = Form(...),
        text: str = Form(...),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token),
) -> DefaultResponse:
    """
    Route that creates new article.

    :param title: Article title
    :param image: Article image
    :param subtitle: Article subtitle
    :param text: Article text
    :param session: SQLAlchemy session object. (FastAPI dependency)
    :param current_user: Object of user that creates article. (FastAPI dependency)
    :return: None
    """
    return await put_article_view(
        current_user=current_user,
        session=session,
        title=title,
        subtitle=subtitle,
        image=image,
        text=text)
