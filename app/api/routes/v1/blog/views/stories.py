from typing import List

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.default_responses import DefaultResponse
from app.api.routes.v1.blog.utility_classes import GetStoriesResponseModel
from app.api.routes.v1.blog.utils.select import get_last_stories
from app.api.routes.v1.users.utils import get_user_by_id
from app.api.routes.v1.utils.auth import check_is_user_admin
from app.constants import MAX_STORIES_COUNT
from app.database.models.base import Story, StoryItem
from app.utils import S3Manager


async def get_stories_view(session: AsyncSession):
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


async def put_story_view(current_user, session: AsyncSession, images: List[UploadFile], thumbnail: UploadFile, title: str) -> DefaultResponse:
    async with session.begin():
        current_user = await get_user_by_id(user_id=current_user.id, session=session)
        await check_is_user_admin(user=current_user, session=session)
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