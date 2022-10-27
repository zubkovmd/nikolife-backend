"""Default views for recipes routes"""

from datetime import datetime
from typing import List, Optional

from fastapi import Depends, HTTPException, Response, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from starlette import status

from app.api.routes.default_response_models import DefaultResponse, DefaultResponseWithPayload
from app.api.routes.v1.recipes.utility_classes import GetRecipesRecipeResponseModel, RecipeIngredientResponseModel, \
    CreateRecipeIngredientRequestModel, CreateRecipeStepRequestModel, GetRecipesResponseModel, RecipeResponseModel
from app.api.routes.v1.recipes.utils import parse_ingredients_to_pydantic_models, parse_steps_to_pydantic_models, \
    create_recipe_ingredient, get_category_or_create_if_not_exists, create_or_update_recipe_ingredients, \
    update_recipe_steps, update_recipe_categories, parse_categories_to_list, \
    get_recipe_by_id, select_recipes_and_filter_them, build_recipes_output, select_liked_recipes, build_recipe_output, \
    check_is_user_allow_to_modify_recipe, create_new_recipe, update_recipe
from app.api.routes.v1.utils.auth import get_user_by_token
from app.api.routes.v1.utils.service_models import UserModel
from app.constants import ADMIN_GROUP_NAME
from app.database import DatabaseManagerAsync
from app.database.models.base import Users, Recipes, Ingredients, RecipeIngredients, \
    RecipeSteps, RecipeCategories, Groups, association_recipes_categories, \
    RecipeCompilations
from app.utils import S3Manager
from app.log import default_logger


async def get_recipes_view(
        prefer_ingredients: Optional[List[str]],
        exclude_groups: Optional[List[str]],
        include_categories: Optional[List[str]],
        compilation: Optional[str],
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token),
) -> GetRecipesResponseModel:
    """
    View for recipes request

    :param session: SQLAlchemy AsyncSession
    :param current_user: User information object
    :param prefer_ingredients: exclude recipes that don't contain these ingredients
    :param exclude_groups: exclude recipe with this groups
    :param include_categories: exclude recipes that don't have these ingredients
    :param compilation: exclude recipes that not in this compilation
    :return: found recipes list
    """
    async with session.begin():

        # get recipes with selected filters
        recipes = await select_recipes_and_filter_them(
            session=session,
            user_groups=current_user.groups,
            include_categories=include_categories,
            prefer_ingredients=prefer_ingredients,
            compilation=compilation,
            exclude_groups=exclude_groups
        )
        if not recipes:
            return GetRecipesResponseModel(recipes=[])
        # now for each recipe we should make image link and add 'liked' field (it's liked by request user)
        return GetRecipesResponseModel(recipes=build_recipes_output(recipes=recipes, current_user=current_user))


async def get_recipes_by_ingredient_view(
        ingredient_name: str,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token),
) -> GetRecipesResponseModel:
    """
    View for recipes search by ingredient

    :param ingredient_name: name of ingredient
    :param session: SQLAlchemy AsyncSession object
    :param current_user: User information object
    :return: found recipes list
    """
    # get recipes with selected filters
    recipes = await select_recipes_and_filter_them(
        session=session,
        user_groups=current_user.groups,
        prefer_ingredients=[ingredient_name],
    )
    if not recipes:
        return GetRecipesResponseModel(recipes=[])
    # now for each recipe we should make image link and add 'liked' field (it's liked by request user)
    return GetRecipesResponseModel(recipes=build_recipes_output(recipes=recipes, current_user=current_user))


async def get_recipes_by_category_view(
        category_name: str,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token),
) -> GetRecipesResponseModel:
    """
    View for recipes search by category

    :param category_name: name of category
    :param session: SQLAlchemy AsyncSession object
    :param current_user: User information object
    :return: found recipes list
    """
    # get recipes with selected filters
    recipes = await select_recipes_and_filter_them(
        session=session,
        user_groups=current_user.groups,
        include_categories=[category_name],
    )
    if not recipes:
        return GetRecipesResponseModel(recipes=[])
    # now for each recipe we should make image link and add 'liked' field (it's liked by request user)
    return GetRecipesResponseModel(recipes=build_recipes_output(recipes=recipes, current_user=current_user))


async def get_liked_recipes_view(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token)
) -> GetRecipesResponseModel:
    """
    View for search only liked recipes

    :param session: SQLAlchemy AsyncSession object
    :param current_user: User information object
    :return: found recipes list
    """
    async with session.begin():
        recipes = await select_liked_recipes(session, current_user)
        if not recipes:
            return GetRecipesResponseModel(recipes=[])
        return GetRecipesResponseModel(recipes=build_recipes_output(recipes=recipes, current_user=current_user))


async def get_recipe_view(
        recipe_id: int,
        session: AsyncSession,
        current_user: UserModel,
) -> RecipeResponseModel:
    """
    View for request recipe by id.
    If recipe with this id not found throws 404_NOT_FOUND exception
    If user groups is not allowed for recipe throws 401_UNAUTHORIZED exception

    :param recipe_id: id of recipe
    :param session: SQLAlchemy AsyncSession object
    :param current_user: User information object
    :return: found recipe
    """
    async with session.begin():
        recipe = await get_recipe_by_id(recipe_id=recipe_id, session=session)
        if len(set(group.name for group in current_user.groups).intersection(set(i.name for i in recipe.allowed_groups))) == 0:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="У вас нет досутпа к этому рецепту")
        return RecipeResponseModel(**build_recipe_output(recipe=recipe, current_user=current_user))


async def delete_recipe_view(recipe_id: int, session: AsyncSession, current_user) -> DefaultResponse:
    """
    View for recipe deletion by recipe id. If user who try to delete recipe is not recipe creator and not admin, then
    throws 401_UNAUTHORIZED exception

    :param recipe_id: id of recipe that should be deleted
    :param session: SqlAlchemy AsyncSession object
    :param current_user: User information object
    :return: Response with status
    """
    async with session.begin():
        recipe: Recipes = await get_recipe_by_id(recipe_id=recipe_id, session=session)
        await check_is_user_allow_to_modify_recipe(recipe=recipe, current_user=current_user)
        await session.delete(recipe)
        return DefaultResponse(detail="Рецепт был удален")


async def create_recipe_view(
        title: str,
        image: UploadFile,
        time: int,
        complexity: str,
        servings: int,
        categories: str,
        steps: str,
        ingredients: str,
        session: AsyncSession,
        current_user: UserModel,
) -> DefaultResponseWithPayload:
    """
    View for recipe creation

    :param title: Recipe title.
    :param image: Recipe image.
    :param time: Recipe cooking time.
    :param complexity: Recipe complexity (easy / medium / etc...).
    :param servings: Recipe servings.
    :param categories: Recipe categories list (if category do not exist in database, then new category
    with this name will be added to service).
    :param steps: Recipe steps.
    :param ingredients: Recipe ingredients (if ingredient do not exist in database, then new category
    with this name will be added to service).
    :param session: SQLAlchemy AsyncSession object.
    :param current_user: User information object.
    :return: Response with status and recipe id if recipe was created
    """

    # first we need to formalize lists of input parameters to pydantic objects
    ingredients: List[CreateRecipeIngredientRequestModel] = parse_ingredients_to_pydantic_models(ingredients=ingredients)
    steps: List[CreateRecipeStepRequestModel] = parse_steps_to_pydantic_models(steps=steps)
    categories: List[str] = parse_categories_to_list(categories)

    async with session.begin():
        created_recipe_id = await create_new_recipe(
            title=title,
            image=image,
            time=time,
            complexity=complexity,
            servings=servings,
            categories=categories,
            steps=steps,
            ingredients=ingredients,
            session=session,
            current_user=current_user
        )
        return DefaultResponseWithPayload(detail="Рецепт успешно добавлен", payload={"recipe_id": created_recipe_id})


async def update_recipe_view(
    recipe_id: int,
    title: Optional[str],
    image: Optional[UploadFile],
    time: Optional[int],
    complexity: Optional[str],
    servings: Optional[int],
    categories: Optional[str],
    steps: Optional[str],
    ingredients: Optional[str],
    session: AsyncSession,
    current_user: UserModel,
):
    """
    View for recipe update. If user who try to update recipe is not recipe creator and not admin,
    then throws 401_UNAUTHORIZED exception

    :param recipe_id: id of recipe that should be updated
    :param title: If passed, new recipe title
    :param image: If passed, new recipe image
    :param time: If passed, new recipe cooking time
    :param complexity: If passed, new recipe complexity
    :param servings: If passed, new recipe servings count
    :param categories: If passed, new recipe categories
    :param steps: If passed, new recipe steps
    :param ingredients: If passed, new recipe ingredients
    :param session: SQLAlchemy AsyncSession object
    :param current_user: User information object.
    :return: Response with status
    """
    async with session.begin():
        recipe = await get_recipe_by_id(recipe_id=recipe_id, session=session)
        await update_recipe(
            recipe=recipe,
            title=title,
            image=image,
            time=time,
            complexity=complexity,
            servings=servings,
            categories=categories,
            steps=steps,
            ingredients=ingredients,
            session=session,
            current_user=current_user
        )

        return DefaultResponse(detail="Рецепт обновлен")

