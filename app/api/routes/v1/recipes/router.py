"""
Recipes router module. Contains all routes that interact with recipes.
"""

from typing import List, Optional, Union

from fastapi import Depends, UploadFile, Form, File, APIRouter, Body, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.default_response_models import DefaultResponse, DefaultResponseWithPayload
from app.api.routes.v1.recipes.utility_classes import (
    GetRecipesResponseModel, RecipeResponseModel, RecipeCategoriesResponseModel,
    RecipeLikesRequestModel, FindResponseModel, RecipeCompilationsResponseModel,
    CreateCompilationRequestModel, GetIngredientsResponseModel, GetDimensionsResponseModel,
    GetIngredientGroupsResponseModel, GetIngredientsWithGroupsResponseModel, RecipeOneCompilationResponseModel,
    UpdateCompilationRequestModel, RecipeCategoryResponseModel)
from app.api.routes.v1.recipes.utils import get_category_image
from app.api.routes.v1.recipes.views.default import get_recipes_view, get_recipe_view, delete_recipe_view, \
    create_recipe_view, update_recipe_view, get_liked_recipes_view, get_recipes_by_ingredient_view, \
    get_recipes_by_category_view

from app.api.routes.v1.recipes.views.utility import get_recipes_categories_view, get_ingredients_view, \
    get_dimensions_view, get_ingredients_groups_view, toggle_recipe_like_view, \
    find_all_view, get_recipes_compilations_view, create_recipes_compilation_view, get_ingredients_with_groups_view, \
    get_one_compilation_view, update_recipes_compilation_view, delete_recipes_compilation_view
from app.api.routes.v1.utils.auth import get_user_by_token, get_admin_by_token, get_user_by_token_or_none
from app.api.routes.v1.utils.service_models import UserModel
from app.api.routes.v1.utils.utility import build_full_path
from app.database import DatabaseManagerAsync
from app.database.models.base import RecipeCategories
from app.utils import S3Manager

router = APIRouter(prefix="/recipes")


@router.get("/", response_model=GetRecipesResponseModel)
async def get_recipes(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: Optional[UserModel] = Depends(get_user_by_token_or_none),
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
        current_user: UserModel = Depends(get_user_by_token_or_none)
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


@router.delete("/{recipe_id}", response_model=DefaultResponse)
async def delete_recipe(
        recipe_id: int,
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
        allowed_groups: Optional[str] = Form(None),
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
    :param allowed_groups: List of user groups allowed to watch this recipe
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
                                    allowed_groups=allowed_groups,
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
        allowed_groups: Optional[str] = Form(None),
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
    :param allowed_groups: List of user groups allowed to watch this recipe. (Optional, model field ingredients will be changed if value passed).
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
                                    allowed_groups=allowed_groups,
                                    session=session,
                                    current_user=current_user)


@router.get("/categories", response_model=RecipeCategoriesResponseModel)
async def get_recipes_categories(
        current_user: UserModel = Depends(get_user_by_token),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
):
    """
    Route returns all recipe categories available in service.

    :param current_user: current user model
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with available categories.
    """
    return await get_recipes_categories_view(current_user=current_user, session=session)


@router.post("/categories", response_model=DefaultResponse)
async def create_recipe_category(
        name: str = Form(...),
        image: Optional[UploadFile] = None,
        current_user: UserModel = Depends(get_admin_by_token),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
):
    """
    Route returns category info

    :param name: category name
    :param image: category image
    :param current_user: current user data
    :param session: SQLAlchemy AsyncSession object.
    :return: Category info
    """
    async with session.begin():
        category = await RecipeCategories.get_by_name(name=name, session=session)
        if category:
            raise HTTPException(status_code=409, detail="Такая категория уже существует")
        category = await RecipeCategories.get_by_name_or_create(name=name, session=session)
        if image:
            filename = build_full_path(f"{current_user.username}/categories/{name}", image)
            S3Manager.get_instance().send_image_shaped(image=image, base_filename=filename)
            category.image = filename
        session.add(category)
        return DefaultResponse(detail="Категория добавлена")


@router.get("/categories/{category_id}", response_model=RecipeCategoryResponseModel)
async def get_recipe_category(
        category_id: int,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
):
    """
    Route returns category info

    :param category_id: category id
    :param session: SQLAlchemy AsyncSession object.
    :return: Category info
    """
    async with session.begin():
        category = await RecipeCategories.get_by_id(category_id=category_id, session=session)
        category = category.__dict__
        category["image"] = await get_category_image(category=category["name"], session=session)
        return RecipeCategoryResponseModel(**category)


@router.patch("/categories", response_model=DefaultResponse)
async def update_recipe_category(
        category_id: int = Form(...),
        name: Optional[str] = Form(None),
        image: Optional[UploadFile] = Form(None),
        current_user: UserModel = Depends(get_admin_by_token),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
):
    """
    Route returns category info

    :param image: new category image
    :param name: new category name
    :param category_id: category id
    :param current_user: current user
    :param session: SQLAlchemy AsyncSession object.
    :return: Category info
    """
    async with session.begin():
        category = await RecipeCategories.get_by_id(category_id=category_id, session=session)
        if name:
            category.name = name
        if image:
            filename = build_full_path(f"{current_user.username}/categories/{name}", image)
            S3Manager.get_instance().send_image_shaped(image=image, base_filename=filename)
            category.image = filename
        return DefaultResponse(detail="Рецепт обновлен")


@router.delete("/categories/delete", response_model=DefaultResponse, dependencies=[Depends(get_admin_by_token)])
async def delete_category(
        category_id: int = Form(...),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
):
    async with session.begin():
        await RecipeCategories.delete_by_id(category_id=category_id, session=session)
    return DefaultResponse(detail="Категория удалена")


@router.get("/compilations", response_model=RecipeCompilationsResponseModel)
async def get_recipes_compilations(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: Optional[UserModel] = Depends(get_user_by_token_or_none)
):
    """
    Route returns all recipe compilations.
    Description: Compilation is name for a bunch of grouped recipes by admin. Admin should name it and set an image.

    :param session: SQLAlchemy AsyncSession object.
    :return: Response with available compilations.
    """
    return await get_recipes_compilations_view(session, current_user)


@router.get("/compilations/one/{compilation_id}", response_model=RecipeOneCompilationResponseModel)
async def get_recipes_compilations(
        compilation_id: int,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
):
    """
    Route returns all recipe compilations.
    Description: Compilation is name for a bunch of grouped recipes by admin. Admin should name it and set an image.

    :param compilation_id: id of compilation
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with available compilations.
    """
    return await get_one_compilation_view(session, compilation_id=compilation_id)


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


@router.patch("/compilations", response_model=DefaultResponse)
async def create_recipes_compilation(
        compilation_id: int = Form(...),
        recipe_ids: List[int] = Form(...),
        image: Optional[UploadFile] = File(default=None),
        title: str = Form(...),
        current_user: UserModel = Depends(get_admin_by_token),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
):
    """
    Route for updating existing compilation.
    Description: Compilation is name for a bunch of grouped recipes by admin. Admin should name it and set a image.

    :param recipe_ids: id's of recipes that should appear in new compilation.
    :param image: Compilation image.
    :param title: Compilation title.
    :param current_user: User information object.
    :param session: SQlAlchemy AsyncSession object.
    :return: List of available compilations.
    """
    return await update_recipes_compilation_view(
        current_user,
        # Place form fields in a pydantic model
        UpdateCompilationRequestModel(
            compilation_id=compilation_id,
            recipe_ids=recipe_ids,
            image=image,
            title=title),
        session)


@router.delete("/compilations/del", response_model=DefaultResponse)
async def create_recipes_compilation(
        compilation_id: int,
        current_user: UserModel = Depends(get_admin_by_token),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
):
    """
    Route for deleting existing compilation.
    Description: Compilation is name for a bunch of grouped recipes by admin. Admin should name it and set a image.


    :param compilation_id: compilation id
    :param current_user: User information object.
    :param session: SQlAlchemy AsyncSession object.
    :return: List of available compilations.
    """
    return await delete_recipes_compilation_view(
        current_user=current_user,
        # Place form fields in a pydantic model
        compilation_id=compilation_id,
        session=session)


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


@router.get("/utils/get_available_ingredients_with_groups", response_model=GetIngredientsWithGroupsResponseModel)
async def get_ingredients_with_groups(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
):
    """
    Route will return names of all ingredients registered in this service.Check
    app.database.models.base -> RecipeIngredients for additional info.

    :param session: SQLAlchemy AsyncSession object.
    :return: Response with list of ingredients.
    """
    return await get_ingredients_with_groups_view(session)


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
        current_user: Optional[UserModel] = Depends(get_user_by_token_or_none),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
):
    """
    Route will return result of search by string in models: Recipes, Ingredients and RecipeCategories.
    Check view description for additional info.

    :param string_to_find: String for search.
    :param max_returns: Maximum returned rows for each model.
    :param session: SQLAlchemy AsyncSession object.
    :param current_user: User information object.
    :return: Response with found objects for each model.
    """
    return await find_all_view(
        string_to_find=string_to_find,
        max_returns=max_returns,
        current_user=current_user,
        session=session,
    )


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
    return await get_recipes_by_ingredient_view(
        ingredient_name=ingredient_name,
        session=session,
        current_user=current_user
    )


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
