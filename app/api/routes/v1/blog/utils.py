from typing import List, Optional

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.base import Story


async def get_last_stories(session: AsyncSession, stories_count: int) -> Optional[List[Story]]:
    """
    Function returns last X story object

    :param session: AsyncSession object
    :param stories_count: X count limit of returned stories
    :return: Found stories
    """
    stmt = (
        sqlalchemy.select(Story)
        .options(
            selectinload(Story.story_items)
        )
        .order_by(Story.id.desc())
        .limit(stories_count)
    )
    stories = (await session.execute(stmt)).scalars().all()
    return stories
