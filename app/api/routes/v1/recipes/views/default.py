"""Default views for recipes routes"""
from typing import List, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.routes.default_response_models import DefaultResponse, DefaultResponseWithPayload
from app.api.routes.v1.recipes.utility_classes import (
    CreateRecipeIngredientRequestModel,
    CreateRecipeStepRequestModel,
    GetRecipesResponseModel,
    RecipeResponseModel)
from app.api.routes.v1.recipes.utils import (
    parse_ingredients_to_pydantic_models, parse_steps_to_pydantic_models,
    parse_categories_to_list, select_recipes_and_filter_them,
    build_recipes_output, build_recipe_output, check_is_user_allow_to_modify_recipe,
    create_new_recipe, update_recipe, select_liked_recipes)
from app.api.routes.v1.utils.service_models import UserModel
from app.constants import ADMIN_GROUP_NAME, NOT_AUTHENTICATED_GROUP_NAME
from app.database.models.base import Users, Recipes


async def get_recipes_view(
        prefer_ingredients: Optional[List[str]],
        exclude_groups: Optional[List[str]],
        include_categories: Optional[List[str]],
        compilation: Optional[str],
        session: AsyncSession,
        current_user: Optional[UserModel],
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
            user_groups=current_user.groups if current_user else [NOT_AUTHENTICATED_GROUP_NAME],
            include_categories=include_categories,
            prefer_ingredients=prefer_ingredients,
            compilation=compilation,
            exclude_groups=exclude_groups
        )
        if not recipes:
            return GetRecipesResponseModel(recipes=[])
        # now for each recipe we should make image link and add 'liked' field (it's liked by request user)
        current_user: Users = await Users.get_by_id(user_id=current_user.id, session=session, join_tables=[Users.groups]) if current_user else None
        return GetRecipesResponseModel(recipes=build_recipes_output(recipes=recipes, current_user=current_user))


async def get_recipes_by_ingredient_view(
        ingredient_name: str,
        session: AsyncSession,
        current_user: UserModel,
) -> GetRecipesResponseModel:
    """
    View for recipes search by ingredient

    :param ingredient_name: name of ingredient
    :param session: SQLAlchemy AsyncSession object
    :param current_user: User information object
    :return: found recipes list
    """
    # get recipes with selected filters
    recipes = await Recipes.get_all_with_ingredients(
        session=session,
        user_groups=current_user.groups,
        prefer_ingredients=[ingredient_name],
    )
    if not recipes:
        return GetRecipesResponseModel(recipes=[])
    # now for each recipe we should make image link and add 'liked' field (it's liked by request user)
    current_user: Users = await Users.get_by_id(user_id=current_user.id, session=session)
    return GetRecipesResponseModel(recipes=build_recipes_output(recipes=recipes, current_user=current_user))


async def get_recipes_by_category_view(
        category_name: str,
        session: AsyncSession,
        current_user: UserModel,
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
    current_user: Users = await Users.get_by_id(user_id=current_user.id, session=session, join_tables=[
        Users.groups
    ])
    return GetRecipesResponseModel(recipes=build_recipes_output(recipes=recipes, current_user=current_user))


async def get_liked_recipes_view(
        session: AsyncSession,
        current_user: UserModel
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
        current_user: Users = await Users.get_by_id(user_id=current_user.id, session=session)
        return GetRecipesResponseModel(recipes=build_recipes_output(recipes=recipes, current_user=current_user))


async def get_recipe_view(
        recipe_id: int,
        session: AsyncSession,
        current_user: Optional[UserModel],
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
        recipe = await Recipes.get_by_id(
            recipe_id=recipe_id,
            session=session,
            join_tables=[
                "*"
            ]
        )
        if current_user and ADMIN_GROUP_NAME not in current_user.groups and len(
                set(group for group in current_user.groups)
                .intersection(set(i.name for i in recipe.allowed_groups))
        ) == 0:
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
        recipe: Recipes = await Recipes.get_by_id(recipe_id=recipe_id, session=session)
        await check_is_user_allow_to_modify_recipe(recipe=recipe, current_user=current_user, session=session)
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
        allowed_groups: Optional[str],
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
    :param allowed_groups: List of user groups allowed to watch this recipe
    :param session: SQLAlchemy AsyncSession object.
    :param current_user: User information object.
    :return: Response with status and recipe id if recipe was created
    """

    # first we need to formalize lists of input parameters to pydantic objects
    ingredients: List[CreateRecipeIngredientRequestModel] = parse_ingredients_to_pydantic_models(
        ingredients=ingredients)
    steps: List[CreateRecipeStepRequestModel] = parse_steps_to_pydantic_models(steps=steps)
    categories: List[str] = parse_categories_to_list(categories)
    allowed_groups = eval(allowed_groups) if allowed_groups else None

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
            allowed_groups=allowed_groups,
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
    allowed_groups: Optional[str],
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
    :param allowed_groups: List of user groups allowed to watch this recipe
    :param session: SQLAlchemy AsyncSession object
    :param current_user: User information object.
    :return: Response with status
    """
    async with session.begin():
        recipe = await Recipes.get_by_id(
            recipe_id=recipe_id,
            session=session,
            join_tables=[
                Recipes.compilations, Recipes.allowed_groups, Recipes.ingredients,
                Recipes.steps, Recipes.categories, Recipes.user
            ]
        )
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
            allowed_groups=allowed_groups,
            session=session,
            current_user=current_user
        )

        return DefaultResponse(detail="Рецепт обновлен")
