"""Article routes views"""
from typing import Optional

import sqlalchemy
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.routes.default_response_models import DefaultResponse
from app.api.routes.v1.blog.models import GetArticlesResponseModel
from app.api.routes.v1.utils.service_models import UserModel
from app.api.routes.v1.utils.utility import build_full_path
from app.database.models.base import Users, Articles
import app.database.models.base as schema
from app.utils import S3Manager
from app.utils.utility import filter_dict_with_key_list


async def create_article_view(
        title: str,
        image: UploadFile,
        subtitle: str,
        text: str,
        session: AsyncSession,
        admin_user: UserModel,
) -> DefaultResponse:
    """
    View that creates new article

    :param title: Article title
    :param image: Article image
    :param subtitle: Article subtitle
    :param text: Article text
    :param session: SQLAlchemy session object
    :param admin_user: User information object
    :return: DefaultResponse
    """
    async with session.begin():
        user_model = await Users.get_by_id(user_id=admin_user.id, session=session)
        await Articles.create(
            session=session,
            title=title,
            image=image,
            subtitle=subtitle,
            article_text=text,
            creator=user_model
        )
        return DefaultResponse(status_code=200, detail="Статья создана")


async def update_article_view(
        article_id: int,
        title: str,
        image: Optional[UploadFile],
        subtitle: str,
        text: str,
        session: AsyncSession,
        admin_user: UserModel,
) -> DefaultResponse:
    """
    View that updates article

    :param article_id: Article id
    :param title: Article title
    :param image: Article image
    :param subtitle: Article subtitle
    :param text: Article text
    :param session: SQLAlchemy session object
    :param admin_user: User information object
    :return: DefaultResponse
    """
    async with session.begin():
        article = await Articles.get_by_id(session=session, article_id=article_id)
        previous: dict = filter_dict_with_key_list(article.__dict__, ["title", "image", "subtitle", "text"])
        new_article_state = await Articles.update(
            session=session,
            article_id=article_id,
            title=title,
            image=image,
            subtitle=subtitle,
            article_text=text,
            username=admin_user.username
        )
        updated: dict[str] = filter_dict_with_key_list(new_article_state.__dict__,
                                                       ["title", "image", "subtitle", "text"])
        admin_user.log_info(f"User update article ({article_id=}). Old: {previous}, New: {updated}")
        return DefaultResponse(status_code=200, detail="Статья обновлена")


async def delete_article_view(
        article_id: int,
        session: AsyncSession,
        current_user: UserModel,
) -> DefaultResponse:
    """
    View that deletes article

    :param article_id: Article id
    :param session: SQLAlchemy session object
    :param current_user: User information object
    :return: DefaultResponse
    """
    async with session.begin():
        await Articles.delete(session=session, article_id=article_id)
        current_user.log_info(f"Deleted article {article_id=}")
        return DefaultResponse(status_code=200, detail="Статья удалена")


async def get_articles_view(
        articles_count: int,
        session: AsyncSession,
        full_time: bool = False,
) -> GetArticlesResponseModel:
    """
    View that returns *articles_count* last articles

    :param articles_count: Count of returned articles
    :param session: SQLAlchemy session object
    :param full_time: is a full time needed
    :return: Article model
    """
    async with session.begin():
        articles = await Articles.get_all(session=session, limit=articles_count)
        return GetArticlesResponseModel(
            articles=[
                {
                    "id": article.id,
                    "title": article.title,
                    "subtitle": article.subtitle,
                    "created_at": article.created_at.strftime(u'%Y-%m-%dT%H:%M') if full_time
                    else article.created_at.strftime(u'%d %B %Y'),
                    "text": article.text,
                    "image": S3Manager.get_instance().get_url(f"{article.image}_med.jpg"),
                    "user_id": article.user.id,
                }
                for article
                in articles
            ]
        )
