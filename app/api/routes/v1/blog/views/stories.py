"""Story routes views"""

from typing import List

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.default_response_models import DefaultResponse
from app.api.routes.v1.blog.models import GetStoriesResponseModel
from app.api.routes.v1.blog.utils import get_last_stories
from app.api.routes.v1.users.utils import get_user_by_id
from app.api.routes.v1.utils.auth import check_is_user_admin
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
                    "title": story.title,
                    "thumbnail": S3Manager.get_instance().get_url(story.thumbnail),
                    "images": [S3Manager.get_instance().get_url(story_item.image) for story_item in story.story_items]
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
        thumbnail_filename = f"{current_user.username}/stories/{title}/{thumbnail.filename}"
        S3Manager.get_instance().send_memory_file_to_s3(thumbnail.file, thumbnail_filename)
        new_story.thumbnail = thumbnail_filename
        for image in images:
            filename = f"{current_user.username}/stories/{title}/{image.filename}"
            S3Manager.get_instance().send_memory_file_to_s3(image.file, filename)
            new_story.story_items.append(StoryItem(image=filename))
        session.add(new_story)
        return DefaultResponse(detail="Story добавлена")
