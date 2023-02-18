"""Story routes views"""

from typing import List

import sqlalchemy
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.routes.default_response_models import DefaultResponse
from app.api.routes.v1.blog.models import GetStoriesResponseModel
from app.api.routes.v1.blog.utils import get_last_stories
from app.api.routes.v1.utils.utility import get_raw_filename
from app.constants import MAX_STORIES_COUNT
from app.database.models.base import Story, StoryItem
from app.utils import S3Manager


async def get_stories_view(session: AsyncSession):
    """
    Views for stories request. Returns last app.constants.MAX_STORIES_COUNT stories if at least one exists,
    else returns blank list.

    :param session: SQLAlchemy AsyncSession object
    :return: Response with stories
    """
    async with session.begin():
        stories = await get_last_stories(session, MAX_STORIES_COUNT)
        return GetStoriesResponseModel(**{
            "stories": [
                {
                    "id": story.id,
                    "title": story.title,
                    "thumbnail": S3Manager.get_instance().get_url(f"{story.thumbnail}_small.jpg"),
                    "images": [
                        S3Manager.get_instance().get_url(f"{story_item.image}_big.jpg")
                        for story_item in story.story_items
                    ]
                }
                for story
                in stories]
        })


async def put_story_view(
        current_user,
        session: AsyncSession,
        images: List[UploadFile],
        thumbnail: UploadFile,
        title: str
) -> DefaultResponse:
    """
    View for story adding route

    :param current_user: User information object.
    :param session: SQLAlchemy AsyncSession object.
    :param images: Story images.
    :param thumbnail: Story thumbnail.
    :param title: Story title.
    :return: Response with status
    """
    async with session.begin():
        new_story = Story(title=title)
        thumbnail_filename = f"{current_user.username}/stories/{title}/{get_raw_filename(thumbnail.filename)}"
        S3Manager.get_instance().send_image_shaped(image=thumbnail, base_filename=thumbnail_filename)
        new_story.thumbnail = thumbnail_filename
        for image in images:
            story_image_filename = f"{current_user.username}/stories/{title}/{get_raw_filename(image.filename)}"
            S3Manager.get_instance().send_image_shaped(image=image, base_filename=story_image_filename)
            new_story.story_items.append(StoryItem(image=story_image_filename))
        session.add(new_story)
        return DefaultResponse(detail="Story добавлена")


async def delete_story_view(
        current_user,
        story_id: int,
        session: AsyncSession,
) -> DefaultResponse:
    """
    View for story adding route

    :param current_user: User information object.
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with status
    """
    async with session.begin():
        response = await session.execute(sqlalchemy.select(Story).filter(Story.id == story_id))
        story = response.scalars().first()
        if not story:
            raise HTTPException(status_code=404,
                                detail=f"Стори с id {story_id} не найдена")
        await session.delete(story)
        return DefaultResponse(detail="Story добавлена")


