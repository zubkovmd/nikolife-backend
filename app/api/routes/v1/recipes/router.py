"""
Recipes router module. Contains all routes that interact with recipes.
"""

from typing import List, Dict, Optional, Union

from fastapi import Depends, Response, UploadFile, Form, File, APIRouter, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.default_response_models import DefaultResponse, DefaultResponseWithPayload
from app.api.routes.v1.recipes.utility_classes import GetRecipesResponseModel, RecipeResponseModel, \
    RecipeCategoriesResponseModel, RecipeLikesRequestModel, GetRecipesRequestModel, FindResponseModel, FindRequestModel, \
    RecipeCompilationResponseModel, RecipeCompilationsResponseModel, CreateCompilationRequestModel, \
    GetIngredientsResponseModel, GetDimensionsResponseModel, GetIngredientGroupsResponseModel
from app.api.routes.v1.recipes.views.default import get_recipes_view, get_recipe_view, delete_recipe_view, \
    create_recipe_view, update_recipe_view, get_liked_recipes_view, get_recipes_by_ingredient_view, \
    get_recipes_by_category_view

from app.api.routes.v1.recipes.views.utility import get_recipes_categories_view, get_ingredients_view, \
    get_dimensions_view, get_ingredients_groups_view, toggle_recipe_like_view, \
    find_all_view, get_recipes_compilations_view, create_recipes_compilation_view
from app.api.routes.v1.utils.auth import get_user_by_token, get_user_by_token, get_admin_by_token
from app.api.routes.v1.utils.service_models import UserModel
from app.database import DatabaseManagerAsync

from app.database.models.base import Users

router = APIRouter(prefix="/recipes")


@router.get("/", response_model=GetRecipesResponseModel)
async def get_recipes(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token),
        prefer_ingredients: Union[List[str], None] = Query(default=None),
        exclude_groups: Union[List[str], None] = Query(default=None),
        include_categories: Union[List[str], None] = Query(default=None),
        compilation: Union[str, None] = Query(default=None)
) -> GetRecipesResponseModel:
    """
    Route that search all recipes that stored in database and return them with filtering.

    :param session: SQLAlchemy AsyncSession
    :param current_user: User information object
    :param prefer_ingredients: Exclude recipes that don't contain these ingredients
    :param exclude_groups: Exclude recipe with this groups
    :param include_categories: Exclude recipes that don't have these ingredients
    :param compilation: Exclude recipes that not in this compilation
    :return: Recipes list
    """
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
        current_user: UserModel = Depends(get_user_by_token),
):
    """
    Route that returns liked (bu request user) recipes.

    :param session: SQLAlchemy AsyncSession object.
    :param current_user: User information object.
    :return: Recipes list.
    """
    return await get_liked_recipes_view(session, current_user)


@router.get("/one/{recipe_id}", response_model=RecipeResponseModel)
async def get_recipe(
        recipe_id: int,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token)
):
    """
    Route that returns recipe by recipe id. If recipe not found, then
    404_NOT_FOUND will be throwed.

    :param recipe_id: Id of recipe.
    :param session: SQLAlchemy AsyncSession object.
    :param current_user: User information object.
    :return: Found recipe.
    """
    return await get_recipe_view(recipe_id=recipe_id, session=session, current_user=current_user)


@router.delete("/", response_model=DefaultResponse)
async def delete_recipe(
        recipe_id: int = Body(..., embed=True),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token),
):
    """
    Route for recipe deletion.

    :param recipe_id: Id of recipe.
    :param session: SQLAlchemy AsyncSession object.
    :param current_user: User information object.
    :return: Response with status.
    """
    return await delete_recipe_view(recipe_id=recipe_id, session=session, current_user=current_user)


@router.post("/", response_model=DefaultResponseWithPayload)
async def create_recipe(
        title: str = Form(),
        image: UploadFile = File(default=None),
        time: int = Form(),
        complexity: str = Form(),
        servings: int = Form(),
        categories: str = Form(),
        steps: str = Form(),
        ingredients: str = Form(),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_admin_by_token)):
    """
    Route for adding new recipe.

    :param title: Recipe title.
    :param image: Recipe image.
    :param time: Recipe cooking time.
    :param complexity: Recipe complexity (easy / medium / etc...).
    :param servings: Recipe servings count.
    :param categories: Recipe categories.
    :param steps: Recipe steps.
    :param ingredients: Recipe ingredients.
    :param session: SQLAlchemy AsyncSession object.
    :param current_user: User information object.
    :return: Response with status and added recipe id.
    """
    return await create_recipe_view(title=title,
                                    image=image,
                                    time=time,
                                    complexity=complexity,
                                    servings=servings,
                                    categories=categories,
                                    steps=steps,
                                    ingredients=ingredients,
                                    session=session,
                                    current_user=current_user)


@router.patch("/", response_model=DefaultResponse)
async def update_recipe(
        recipe_id: int = Form(None),
        title: Optional[str] = Form(None),
        image: Optional[UploadFile] = File(default=None),
        time: Optional[int] = Form(None),
        complexity: Optional[str] = Form(None),
        servings: Optional[int] = Form(None),
        categories: Optional[str] = Form(None),
        steps: Optional[str] = Form(None),
        ingredients: Optional[str] = Form(None),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token),
):
    """
    Route for updating recipe information.

    :param recipe_id: Id of recipe that should be updated.
    :param title: New recipe title. (Optional, model field title will be changed if value passed).
    :param image: New recipe image. (Optional, model field image will be changed if value passed).
    :param time: New recipe cooking time. (Optional, model field time will be changed if value passed).
    :param complexity: New recipe complexity. (Optional, model field complexity will be changed if value passed).
    :param servings: New recipe servings. (Optional, model field servings will be changed if value passed).
    :param categories: New recipe categories. (Optional, model field categories will be changed if value passed).
    :param steps: New recipe steps. (Optional, model field steps will be changed if value passed).
    :param ingredients: New recipe ingredients. (Optional, model field ingredients will be changed if value passed).
    :param session: SQLAlchemy AsyncSession object.
    :param current_user: User information object.
    :return: Response with status
    """
    return await update_recipe_view(recipe_id=recipe_id,
                                    title=title,
                                    image=image,
                                    time=time,
                                    complexity=complexity,
                                    servings=servings,
                                    categories=categories,
                                    steps=steps,
                                    ingredients=ingredients,
                                    session=session,
                                    current_user=current_user)


@router.get("/categories", response_model=RecipeCategoriesResponseModel)
async def get_recipes_categories(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
):
    """
    Route returns all recipe categories available in service.

    :param session: SQLAlchemy AsyncSession object.
    :return: Response with available categories.
    """
    return await get_recipes_categories_view(session)


@router.get("/compilations", response_model=RecipeCompilationsResponseModel)
async def get_recipes_compilations(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
):
    """
    Route returns all recipe compilations.
    Description: Compilation is name for a bunch of grouped recipes by admin. Admin should name it and set an image.

    :param session: SQLAlchemy AsyncSession object.
    :return: Response with available compilations.
    """
    return await get_recipes_compilations_view(session)


@router.post("/compilations", response_model=DefaultResponse)
async def create_recipes_compilation(
        recipe_ids: List[int] = Form(...),
        image: UploadFile = Form(...),
        title: str = Form(...),
        current_user: UserModel = Depends(get_admin_by_token),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
):
    """
    Route for creating new compilation.
    Description: Compilation is name for a bunch of grouped recipes by admin. Admin should name it and set a image.

    :param recipe_ids: id's of recipes that should appear in new compilation.
    :param image: Compilation image.
    :param title: Compilation title.
    :param current_user: User information object.
    :param session: SQlAlchemy AsyncSession object.
    :return: List of available compilations.
    """
    return await create_recipes_compilation_view(
        current_user,
        # Place form fields in a pydantic model
        CreateCompilationRequestModel(
            recipe_ids=recipe_ids,
            image=image,
            title=title),
        session)


@router.post("/toggle_recipe_like", response_model=DefaultResponse)
async def toggle_recipe_like(
        recipe: RecipeLikesRequestModel,
        current_user: UserModel = Depends(get_user_by_token),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
):
    """
    Route that toggles recipe 'liked' state for user. First call will 'likes' recipe and this recipe will appear
    in response for route ('/liked', get_liked_recipes(...)). Second call will remove this recipe from user likes.

    :param recipe: Recipe object that contains recipe id.
    :param current_user: User information object.
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with status.
    """
    return await toggle_recipe_like_view(recipe=recipe, current_user=current_user, session=session)


@router.get("/utils/get_available_ingredients", response_model=GetIngredientsResponseModel)
async def get_ingredients(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
):
    """
    Route will return names of all ingredients registered in this service.Check
    app.database.models.base -> RecipeIngredients for additional info.

    :param session: SQLAlchemy AsyncSession object.
    :return: Response with list of ingredients.
    """
    return await get_ingredients_view(session)


@router.get("/utils/get_available_dimensions", response_model=GetDimensionsResponseModel)
async def get_dimensions(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
):
    """
    Route will return of all dimensions registered in this service.
    Check app.database.models.base -> RecipeDimensions for additional info.

    :param session: SQLAlchemy AsyncSession object.
    :return: Response with list of ingredients.
    """
    return await get_dimensions_view(session)


@router.get("/utils/get_available_ingredients_groups", response_model=GetIngredientGroupsResponseModel)
async def get_ingredients_groups(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
):
    """
    Route will return of all ingredient groups registered in this service.
    Check app.database.models.base -> IngredientsGroups for additional info.

    :param session: SQLAlchemy AsyncSession object.
    :return: Response with list of ingredients.
    """
    return await get_ingredients_groups_view(session)


@router.get("/utils/find", response_model=FindResponseModel)
async def find_all(
        string_to_find: str,
        max_returns: int = 5,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
):
    """
    Route will return result of search by string in models: Recipes, Ingredients and RecipeCategories.
    Check view description for additional info.

    :param string_to_find: String for search.
    :param max_returns: Maximum returned rows for each model.
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with found objects for each model.
    """
    return await find_all_view(string_to_find=string_to_find, max_returns=max_returns, session=session)


@router.get("/get_recipes_by_ingredient", response_model=GetRecipesResponseModel)
async def get_recipes_by_ingredient(
        ingredient_name: str,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token),
):
    """
    Route will search recipes by ingredient name.

    :param ingredient_name: Name of a ingredient.
    :param session: SQLAlchemy AsyncSession object.
    :param current_user: User information object.
    :return: Found recipes.
    """
    return await get_recipes_by_ingredient_view(ingredient_name=ingredient_name, session=session, current_user=current_user)


@router.get("/get_recipes_by_category", response_model=GetRecipesResponseModel)
async def get_recipes_by_category(
        category_name: str,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token),
):
    """
    Route will search recipes by category name.

    :param category_name: Name of a ingredient.
    :param session: SQLAlchemy AsyncSession object.
    :param current_user: User information object.
    :return: Found recipes.
    """
    return await get_recipes_by_category_view(category_name=category_name, session=session, current_user=current_user)
