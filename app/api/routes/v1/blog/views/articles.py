"""Article routes views"""
from typing import Optional

import sqlalchemy
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from app.api.routes.default_response_models import DefaultResponse
from app.api.routes.v1.blog.models import GetArticlesResponseModel
from app.api.routes.v1.users.utils import get_user_by_id
from app.api.routes.v1.utils.utility import get_raw_filename
from app.constants import ADMIN_GROUP_NAME
from app.database.models.base import Users, Articles
from app.utils import S3Manager


async def put_article_view(
        title: str,
        image: UploadFile,
        subtitle: str,
        text: str,
        session: AsyncSession,
        current_user: Users,
) -> DefaultResponse:
    """
    View that creates new article

    :param title: Article title
    :param image: Article image
    :param subtitle: Article subtitle
    :param text: Article text
    :param session: SQLAlchemy session object
    :param current_user: User information object
    :return: DefaultResponse
    """
    async with session.begin():
        current_user = await get_user_by_id(user_id=current_user.id, session=session)
        filename = f"{current_user.username}/blog/{get_raw_filename(image.filename)}"
        S3Manager.get_instance().send_image_shaped(image=image, base_filename=filename)

        new_article = Articles(
            title=title,
            subtitle=subtitle,
            text=text,
            image=filename,
            user=current_user
        )
        session.add(new_article)
        return DefaultResponse(status_code=200, detail="Статья создана")


async def update_article_view(
        article_id: int,
        title: str,
        image: Optional[UploadFile],
        subtitle: str,
        text: str,
        session: AsyncSession,
        current_user: Users,
) -> DefaultResponse:
    """
    View that creates new article

    :param title: Article title
    :param image: Article image
    :param subtitle: Article subtitle
    :param text: Article text
    :param session: SQLAlchemy session object
    :param current_user: User information object
    :return: DefaultResponse
    """
    async with session.begin():
        resp = await session.execute(sqlalchemy.select(Articles).filter(Articles.id == article_id))
        article = resp.scalars().first()
        if not current_user.id == article.user_id and not ADMIN_GROUP_NAME in current_user.groups:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail=f"Вы не можете редактировать данную статью")
        if not article:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Статья с id {article_id} не найдена")

        article.title = title
        article.subtitle = subtitle
        article.text = text
        if image:
            filename = f"{current_user.username}/blog/{get_raw_filename(image.filename)}"
            S3Manager.get_instance().send_image_shaped(image=image, base_filename=filename)
            article.image = filename
        return DefaultResponse(status_code=200, detail="Статья обновлена")


async def delete_article_view(
        article_id: int,
        session: AsyncSession,
        current_user: Users,
) -> DefaultResponse:
    """
    View that creates new article

    :param title: Article title
    :param image: Article image
    :param subtitle: Article subtitle
    :param text: Article text
    :param session: SQLAlchemy session object
    :param current_user: User information object
    :return: DefaultResponse
    """
    async with session.begin():
        resp = await session.execute(sqlalchemy.select(Articles).filter(Articles.id == article_id))
        article = resp.scalars().first()
        if not current_user.id == article.user_id and ADMIN_GROUP_NAME not in current_user.groups:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail=f"Вы не можете редактировать данную статью")
        if not article:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Статья с id {article_id} не найдена")

        await session.delete(article)
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
    :return: Article model
    """
    async with session.begin():
        articles = (
            await session.execute(
                sqlalchemy.select(Articles)
                .order_by(Articles.id.desc())
                .limit(articles_count)
                .options(selectinload(Articles.user)))
        ).scalars().all()
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