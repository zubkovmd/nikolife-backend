from typing import List, Union

from fastapi import Depends, APIRouter, Query, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.default_responses import DefaultResponse
from app.api.routes.v1.blog.utility_classes import GetStoriesResponseModel, PutStoriesResponseModel
from app.api.routes.v1.blog.views.stories import get_stories_view, put_story_view
from app.api.routes.v1.recipes.utility_classes import GetRecipesResponseModel
from app.api.routes.v1.recipes.views.default import get_recipes_view
from app.api.routes.v1.users.utils import get_user_by_id
from app.api.routes.v1.utils.auth import get_current_active_user, check_is_user_admin
from app.database.manager import manager
from app.database.models.base import Users

router = APIRouter(prefix="/blog")


@router.get("/stories", response_model=GetStoriesResponseModel)
async def get_stories(
        session: AsyncSession = Depends(manager.get_session_object),
        current_user: Users = Depends(get_current_active_user),
):
    return await get_stories_view(session)


@router.put("/stories", response_model=DefaultResponse)
async def put_story(
        # story_object: PutStoriesResponseModel,
        title: str = Form(...),
        images: List[UploadFile] = Form(...),
        session: AsyncSession = Depends(manager.get_session_object),
        current_user: Users = Depends(get_current_active_user),
):
    return await put_story_view(current_user=current_user, session=session, title=title, images=images)