"""Article routes views"""

import sqlalchemy
from fastapi import Form, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.routes.default_response_models import DefaultResponse
from app.api.routes.v1.blog.models import GetArticlesResponseModel
from app.api.routes.v1.users.utils import get_user_by_id
from app.api.routes.v1.utils.utility import get_raw_filename
from app.constants import MAX_ARTICLES_COUNT
from app.database.models.base import Users, Articles
from app.utils import S3Manager
from PIL import Image, ImageOps
import locale
# locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')


async def get_articles_view(
        articles_count: int,
        session: AsyncSession,
) -> GetArticlesResponseModel:
    """
    View that returns *articles_count* last articles

    :param articles_count: Count of returned articles
    :param session: SQLAlchemy session object
    :return: Article model
    """
    async with session.begin():
        articles = (await session.execute(
            sqlalchemy.select(Articles)
                .order_by(Articles.id.desc())
                .limit(articles_count)
                .options(selectinload(Articles.user))
        )).scalars().all()
        return GetArticlesResponseModel(
            articles=[
                {
                    "title": article.title,
                    "subtitle": article.subtitle,
                    "created_at": article.created_at.strftime(u'%d %B %Y'),
                    "text": article.text,
                    "image": S3Manager.get_instance().get_url(f"{article.image}_med.jpg"),
                    "user_id": article.user.id,
                }
                for article
                in articles
            ]
        )


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
