from typing import List, Dict, Optional, Union

from fastapi import Depends, Response, UploadFile, Form, File, APIRouter, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.default_response_models import DefaultResponse, DefaultResponseWithPayload
from app.api.routes.v1.recipes.utility_classes import GetRecipesResponseModel, RecipeResponseModel, \
    RecipeCategoriesResponseModel, RecipeLikesRequestModel, GetRecipesRequestModel, FindResponseModel, FindRequestModel, \
    RecipeCompilationResponseModel, RecipeCompilationsResponseModel, CreateCompilationRequestModel
from app.api.routes.v1.recipes.views.default import get_recipes_view, get_recipe_view, delete_recipe_view, \
    create_recipe_view, update_recipe_view, get_liked_recipes_view, get_recipes_by_ingredient_view, \
    get_recipes_by_category_view

from app.api.routes.v1.recipes.views.utility import get_recipes_categories_view, get_available_ingredients_view, \
    get_available_dimensions_view, get_available_ingredients_groups_view, toggle_recipe_like_view, \
    remove_recipe_from_likes_view, find_all_view, get_recipes_compilations_view, create_recipes_compilation_view
from app.api.routes.v1.utils.auth import get_user_by_token, get_user_by_token
from app.database import DatabaseManagerAsync

from app.database.models.base import Users

router = APIRouter(prefix="/recipes")


@router.get("/", response_model=GetRecipesResponseModel)
async def get_recipes(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: Users = Depends(get_user_by_token),
        prefer_ingredients: Union[List[str], None] = Query(default=None),
        exclude_groups: Union[List[str], None] = Query(default=None),
        include_categories: Union[List[str], None] = Query(default=None),
        compilation: Union[str, None] = Query(default=None)
):
    return await get_recipes_view(
        prefer_ingredients,
        exclude_groups,
        include_categories,
        compilation,
        session,
        current_user)


@router.get("/liked", response_model=GetRecipesResponseModel)
async def get_liked_recipes(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: Users = Depends(get_user_by_token),
):
    return await get_liked_recipes_view(session, current_user)


@router.get("/one/{recipe_id}", response_model=RecipeResponseModel)
async def get_recipe(
        recipe_id: int,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: Users = Depends(get_user_by_token)):
    return await get_recipe_view(recipe_id=recipe_id, session=session, current_user=current_user)


@router.delete("/", response_model=DefaultResponse)
async def delete_recipe(
        response: Response,
        recipe_id: int = Body(..., embed=True),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: Users = Depends(get_user_by_token), ):
    return await delete_recipe_view(response, recipe_id, session, current_user)


@router.post("/", response_model=DefaultResponseWithPayload)
async def create_recipe(
        response: Response, title: str = Form(), image: UploadFile = File(default=None),
        time: int = Form(),
        complexity: str = Form(),
        servings: int = Form(),
        categories: str = Form(),
        steps: str = Form(),
        ingredients: str = Form(),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: Users = Depends(get_user_by_token)):
    return await create_recipe_view(response, title, image, time, complexity, servings,
                                    categories, steps, ingredients, session, current_user)


@router.patch("/", response_model=DefaultResponse)
async def update_recipe(
        response: Response, recipe_id: int = Form(None), title: Optional[str] = Form(None),
        image: Optional[UploadFile] = File(default=None),
        time: Optional[int] = Form(None), complexity: Optional[str] = Form(None), servings: Optional[int] = Form(None),
        categories: Optional[str] = Form(None), steps: Optional[str] = Form(None),
        ingredients: Optional[str] = Form(None),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: Users = Depends(get_user_by_token),
):
    return await update_recipe_view(response, recipe_id, title, image, time, complexity,
                                    servings, categories, steps, ingredients, session, current_user)


@router.get("/categories", response_model=RecipeCategoriesResponseModel)
async def get_recipes_categories(
        current_user: Users = Depends(get_user_by_token),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)):
    return await get_recipes_categories_view(session)


@router.get("/compilations", response_model=RecipeCompilationsResponseModel)
async def get_recipes_compilations(
        current_user: Users = Depends(get_user_by_token),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)):
    return await get_recipes_compilations_view(session)



@router.post("/compilations", response_model=DefaultResponse)
async def create_recipes_compilation(
        recipe_ids: List[int] = Form(...),
        image: UploadFile = Form(...),
        title: str = Form(...),
        current_user: Users = Depends(get_user_by_token),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
):
    return await create_recipes_compilation_view(current_user, CreateCompilationRequestModel(recipe_ids=recipe_ids, image=image, title=title), session)


@router.post("/toggle_recipe_like", response_model=DefaultResponse)
async def toggle_recipe_like(
        recipe: RecipeLikesRequestModel,
        current_user: Users = Depends(get_user_by_token),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)):
    return await toggle_recipe_like_view(recipe=recipe, current_user=current_user, session=session)


@router.post("/remove_recipe_from_likes", response_model=DefaultResponse)
async def remove_recipe_from_likes(
        recipe: RecipeLikesRequestModel,
        current_user: Users = Depends(get_user_by_token),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)):
    return await remove_recipe_from_likes_view(recipe=recipe, current_user=current_user, session=session)


@router.get("/utils/get_available_ingredients", response_model=Dict[str, List[str]])
async def get_available_ingredients(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)):
    return await get_available_ingredients_view(session)


@router.get("/utils/get_available_dimensions", response_model=Dict[str, List[str]])
async def get_available_dimensions(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)):
    return await get_available_dimensions_view(session)


@router.get("/utils/get_available_ingredients_groups", response_model=Dict[str, List[str]])
async def get_available_ingredients_groups(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)):
    return await get_available_ingredients_groups_view(session)


@router.get("/utils/find", response_model=FindResponseModel)
async def find_all(
        string_to_find: str,
        max_returns: int = 5,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)):
    return await find_all_view(string_to_find=string_to_find, max_returns=max_returns, session=session)


@router.get("/get_recipes_by_ingredient", response_model=GetRecipesResponseModel)
async def get_recipes_by_ingredient(
        ingredient_name: str,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: Users = Depends(get_user_by_token),
):
    return await get_recipes_by_ingredient_view(ingredient_name=ingredient_name, session=session, current_user=current_user)


@router.get("/get_recipes_by_category", response_model=GetRecipesResponseModel)
async def get_recipes_by_ingredient(
        category_name: str,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: Users = Depends(get_user_by_token),
):
    return await get_recipes_by_category_view(category_name=category_name, session=session, current_user=current_user)
