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
from app.utils.s3_service import manager as s3_manager


async def get_stories_view(session: AsyncSession):
    async with session.begin():
        stories = await get_last_stories(session, MAX_STORIES_COUNT)
        if not stories:
            raise HTTPException(status_code=404, detail="Историй нет")
        else:
            return GetStoriesResponseModel(**{
                "stories": [
                    {
                        "title": story.title,
                        "thumbnail": story.story_items[0].image,
                        "images": [story_item.image for story_item in story.story_items]
                    }
                    for story
                    in stories]
            })


async def put_story_view(current_user, session: AsyncSession, images: List[UploadFile], title: str) -> DefaultResponse:
    async with session.begin():
        current_user = await get_user_by_id(user_id=current_user.id, session=session)
        await check_is_user_admin(user=current_user, session=session)
        new_story = Story(title=title)
        for image in images:
            filename = f"{current_user.username}/stories/{title}/{image.filename}"
            s3_manager.send_memory_file_to_s3(image.file, filename)
            new_story.story_items.append(StoryItem(image=filename))
        session.add(new_story)
        return DefaultResponse(detail="Story добавлена")