"""
Utility views for recipe routes
"""

from typing import List

import sqlalchemy
from fastapi import Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from starlette import status

from app.api.routes.default_response_models import DefaultResponse
from app.api.routes.v1.recipes.utility_classes import RecipeLikesRequestModel, FindResponseModel, \
    RecipeFindResponseModel, IngredientFindResponseModel, CategoryFindResponseModel, CreateCompilationRequestModel, \
    RecipeCategoriesResponseModel, RecipeCategoryResponseModel, RecipeCompilationsResponseModel, \
    RecipeCompilationResponseModel, GetIngredientsResponseModel, GetDimensionsResponseModel, \
    GetIngredientGroupsResponseModel
from app.api.routes.v1.recipes.utils import get_recipe_by_id, get_category_image
from app.api.routes.v1.users.utils import get_user_by_username, get_user_by_id
from app.api.routes.v1.utils.auth import get_user_by_token
from app.api.routes.v1.utils.service_models import UserModel
from app.database import DatabaseManagerAsync
from app.database.models.base import RecipeCategories, Ingredients, RecipeDimensions, IngredientsGroups, Users, Recipes, \
    RecipeCompilations
from app.utils import S3Manager


async def get_recipes_categories_view(session: AsyncSession) -> RecipeCategoriesResponseModel:
    """
    View returns all recipe categories in service. As category image service selects
    image of first recipe with image in this category

    :param session: SQLAlchemy AsyncSession
    :return: Response with existing categories.
    """
    async with session.begin():
        # First, found all categories
        stmt = sqlalchemy.select(RecipeCategories.name)
        response = await session.execute(stmt)
        categories = response.fetchall()
        # If categories was found, then for each category we should set image.
        if categories:
            found_categories = []
            for category in categories:
                image = await get_category_image(category=category[0], session=session)
                if image is None:
                    continue
                found_categories.append(RecipeCategoryResponseModel(name=category[0], image=image))
            return RecipeCategoriesResponseModel(categories=found_categories)
        else:
            return RecipeCategoriesResponseModel(categories=[])


async def get_recipes_compilations_view(session: AsyncSession) -> RecipeCompilationsResponseModel:
    """
    View returns all recipe compilations registered in service.

    :param session: SQLALchemy AsyncSession object.
    :return: Response with compilations
    """
    async with session.begin():
        # First, select all existing compilations
        stmt = sqlalchemy.select(RecipeCompilations)
        response = await session.execute(stmt)
        compilations: List[RecipeCompilations] = response.scalars().all()
        # If compilations found, for each we should make link to s3
        if compilations:
            found_compilations = []
            for compilation in compilations:

                found_compilations.append(
                    RecipeCompilationResponseModel(
                        name=compilation.name,
                        image=S3Manager.get_instance().get_url(compilation.image)
                    )
                )
            return RecipeCompilationsResponseModel(compilations=found_compilations)
        else:
            return RecipeCompilationsResponseModel(compilations=[])


async def create_recipes_compilation_view(
        current_user: UserModel,
        request: CreateCompilationRequestModel,
        session: AsyncSession):
    """
    View that creates recipe compilation.
    Description: Compilation is name for a bunch of grouped recipes by admin. Admin should name it and set an image.

    :param current_user: User information object
    :param request: Request with compilation data
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with status
    """
    async with session.begin():
        # First, select all recipes, selected for new compilation
        stmt = sqlalchemy.select(Recipes).where(Recipes.id.in_(request.recipe_ids))
        recipes = (await session.execute(stmt)).scalars().all()
        # Load compilation image to s3
        filename = f"{current_user.username}/compilations/{request.image.filename}"
        S3Manager.get_instance().send_memory_file_to_s3(request.image.file, filename)
        # Add new compilation
        session.add(RecipeCompilations(name=request.title, recipes=recipes, image=filename))
    return DefaultResponse(detail="Подборка добавлена")


async def get_ingredients_view(session: AsyncSession) -> GetIngredientsResponseModel:
    """
    View that returns all ingredients in service.

    :param session: SQLAlchemy AsyncSession object.
    :return: Response with existing ingredients.
    """
    async with session.begin():
        stmt = sqlalchemy.select(Ingredients.name)
        response = await session.execute(stmt)
        ingredients: List[str] = response.fetchall()
        if ingredients:
            ingredients = [i[0] for i in ingredients]
        else:
            ingredients = []
        return GetIngredientsResponseModel(ingredients=ingredients)


async def get_dimensions_view(session: AsyncSession) -> GetDimensionsResponseModel:
    """
    View that returns all dimensions in service.

    :param session: SQLAlchemy AsyncSession object.
    :return: Response with existing dimensions.
    """
    async with session.begin():
        stmt = sqlalchemy.select(RecipeDimensions.name)
        response = await session.execute(stmt)
        dimensions: List[str] = response.fetchall()
        if dimensions:
            dimensions = [i[0] for i in dimensions]
        else:
            dimensions = []
        return GetDimensionsResponseModel(dimensions=dimensions)


async def get_ingredients_groups_view(session: AsyncSession) -> GetIngredientGroupsResponseModel:
    """
    View that returns all ingredient groups in service.

    :param session: SQLAlchemy AsyncSession object.
    :return: Response with existing ingredient groups.
    """
    async with session.begin():
        stmt = sqlalchemy.select(IngredientsGroups.name)
        response = await session.execute(stmt)
        groups: List[str] = response.fetchall()
        if groups:
            groups = [i[0] for i in groups]
        else:
            groups = []
        return GetIngredientGroupsResponseModel(groups=groups)


async def toggle_recipe_like_view(
        recipe: RecipeLikesRequestModel,
        current_user: UserModel = Depends(get_user_by_token),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
) -> DefaultResponse:
    """
    This view is set's recipe to 'liked' state request user did not like it before, if recipe is already liked,
    then like will be unset (row will be deleted for association table USERS-RECIPES).

    :param recipe: Recipe request object that contains recipe id.
    :param current_user: User information object.
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with status
    """
    async with session.begin():
        # First we needs to get mapped user object from database
        current_user = get_user_by_id(session=session, user_id=current_user.id, join_tables=[Users.liked_recipes])
        # Then we need to get recipe object
        recipe = await get_recipe_by_id(recipe_id=recipe.recipe_id, session=session)
        # Now if recipe is not liked, then we should add it to likes
        if recipe not in current_user.liked_recipes:
            current_user.liked_recipes.append(recipe)
            return DefaultResponse(detail="Рецепт добавлен в избранное")
        # If recipe already liked, then we should delete it from likes
        else:
            current_user.liked_recipes.remove(recipe)
            return DefaultResponse(detail="Рецепт удален из избранного")


async def search_by_field(string_to_find, max_returns, model, field, session):
    """
    Utility method that search in selected field in selected model for entries. If there are full compare, then
    method will return only fully compared rows, else it will return **max_returns** rows with substring compares.

    :param string_to_find: String for search.
    :param max_returns: Max returns for semi-compared rows.
    :param model: SQLAlchemy model for search.
    :param field: SQLAlchemy model field for search.
    :param session: SQLAlchemy AsyncSession object.
    :return: List of found objects.
    """
    search_by_full_compare = sqlalchemy.select(model).where(field == string_to_find).limit(1)
    resp = await session.execute(search_by_full_compare)
    resp = resp.scalars().first()
    if resp:
        return [resp]
    else:
        search_by_semi_compare = sqlalchemy.select(model).filter(
            func.lower(field).contains(string_to_find.lower())).limit(max_returns)
        resp = await session.execute(search_by_semi_compare)
        resp = resp.scalars().all()
        if resp:
            return resp
        else:
            return []


async def find_all_view(
        string_to_find: str,
        max_returns: int = 5,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object)
) -> FindResponseModel:
    """
    Method will search string_to_find in all searchable models: recipes, ingredients, recipe categories. First,
    it returns only fully compared database rows for each model. If fully compared rows not found, then it searches
    semi-compared rows.

    :param string_to_find: String for search.
    :param max_returns: Maximum returned rows for each model.
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with found objects for each model.
    """
    async with session.begin():
        response_model = FindResponseModel(recipes=[], ingredients=[], categories=[])

        # FIND IN RECIPES
        search_recipes: List[Recipes] = await search_by_field(string_to_find=string_to_find, max_returns=max_returns,
                                                              model=Recipes, field=Recipes.title, session=session)
        response_model.recipes = [RecipeFindResponseModel(title=i.title, recipe_id=i.id) for i in search_recipes]
        # FIND IN CATEGORIES
        searh_categories: List[RecipeCategories] = await search_by_field(string_to_find=string_to_find,
                                                                         max_returns=max_returns,
                                                                         model=RecipeCategories,
                                                                         field=RecipeCategories.name, session=session)
        response_model.categories = [CategoryFindResponseModel(name=category.name, category_id=category.id) for category
                                     in searh_categories]
        # FIND IN INGREDIENTS
        searh_ingredients: List[Ingredients] = await search_by_field(string_to_find=string_to_find,
                                                                     max_returns=max_returns, model=Ingredients,
                                                                     field=Ingredients.name, session=session)
        response_model.ingredients = [IngredientFindResponseModel(name=ingredient.name, ingredient_id=ingredient.id) for
                                      ingredient in searh_ingredients]

        return response_model
