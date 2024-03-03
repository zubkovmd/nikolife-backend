"""
Utility views for recipe routes
"""
import datetime
import time
from typing import List, Optional

import sqlalchemy
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from app.api.routes.default_response_models import DefaultResponse
from app.api.routes.v1.recipes.utility_classes import (
    RecipeLikesRequestModel, FindResponseModel, RecipeFindResponseModel,
    IngredientFindResponseModel, CategoryFindResponseModel, CreateCompilationRequestModel,
    RecipeCategoriesResponseModel, RecipeCategoryResponseModel, RecipeCompilationsResponseModel,
    RecipeCompilationResponseModel, GetIngredientsResponseModel, GetDimensionsResponseModel,
    GetIngredientGroupsResponseModel, GetIngredientsWithGroupsResponseModel, RecipeOneCompilationResponseModel,
    UpdateCompilationRequestModel)
from app.api.routes.v1.recipes.utils import get_category_image
from app.api.routes.v1.utils.service_models import UserModel
from app.api.routes.v1.utils.utility import build_full_path
from app.constants import PAYED_GROUP_NAME, ADMIN_GROUP_NAME, NOT_AUTHENTICATED_GROUP_NAME
from app.database.models.base import (
    RecipeCategories,
    Ingredients,
    RecipeDimensions,
    IngredientsGroups,
    Users,
    Recipes,
    RecipeCompilations)
from app.utils import S3Manager


async def get_recipes_categories_view(
        session: AsyncSession,
        current_user: Optional[UserModel]
) -> RecipeCategoriesResponseModel:
    """
    View returns all recipe categories in service. As category image service selects
    image of first recipe with image in this category

    :param current_user: current user info
    :param session: SQLAlchemy AsyncSession
    :return: Response with existing categories.
    """
    async with session.begin():
        # First, found all categories
        stmt = (sqlalchemy
                .select(RecipeCategories)
                )
        response = await session.execute(stmt)
        categories: List[RecipeCategories] = response.fetchall()
        # If categories was found, then for each category we should set image.
        categories = [category[0] for category in categories]
        if categories:
            found_categories = []
            for category in categories:
                image = await get_category_image(category=category.name, session=session)
                if image is None and not (current_user and ADMIN_GROUP_NAME in current_user.groups):
                    continue
                found_categories.append(RecipeCategoryResponseModel(id=category.id, name=category.name, image=image))
            return RecipeCategoriesResponseModel(categories=found_categories)
        else:
            return RecipeCategoriesResponseModel(categories=[])


async def get_recipes_compilations_view(
        session: AsyncSession,
        current_user: Optional[UserModel]
) -> RecipeCompilationsResponseModel:
    """
    View returns all recipe compilations registered in service.

    :param current_user: User object
    :param session: SQLALchemy AsyncSession object.
    :return: Response with compilations
    """
    async with session.begin():
        # First, select all existing compilations
        compilations: List[RecipeCompilations] = await RecipeCompilations.get_all(session)
        # Then we should filter compilations that current user can see
        user_groups = current_user.groups if current_user else [NOT_AUTHENTICATED_GROUP_NAME]
        if compilations:
            found_compilations = []
            for compilation in compilations:
                user_can_see_recipes_in_compilation = False
                for recipe in compilation.recipes:
                    if (ADMIN_GROUP_NAME in user_groups) or \
                            len(set(user_groups).intersection(set([group.name for group in recipe.allowed_groups]))) > 0:
                        user_can_see_recipes_in_compilation = True
                if user_can_see_recipes_in_compilation:
                    found_compilations.append(
                        RecipeCompilationResponseModel(
                            compilation_id=compilation.id,
                            name=compilation.name,
                            image=S3Manager.get_instance().get_url(f"{compilation.image}_small.jpg"),
                            position=compilation.position
                        )
                    )
            return RecipeCompilationsResponseModel(compilations=found_compilations)
        else:
            return RecipeCompilationsResponseModel(compilations=[])


async def get_one_compilation_view(session: AsyncSession, compilation_id: int) -> RecipeOneCompilationResponseModel:
    """
    View returns all recipe compilations registered in service.

    :param compilation_id: compilation id
    :param session: SQLALchemy AsyncSession object.
    :return: Response with compilations
    """
    async with session.begin():
        compilation: RecipeCompilations = await RecipeCompilations.get_by_id(
            session=session,
            compilation_id=compilation_id,
            join_tables=[RecipeCompilations.recipes]
        )

        return RecipeOneCompilationResponseModel(
            compilation_id=compilation.id,
            name=compilation.name,
            position=compilation.position,
            image=S3Manager.get_instance().get_url(f"{compilation.image}_small.jpg"),
            recipes=[i.__dict__ for i in compilation.recipes]
        )


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
        # First, load all recipes, selected for new compilation
        recipes_list: List[Recipes] = [
            await Recipes.get_by_id(recipe_id, session)
            for recipe_id
            in request.recipe_ids
        ]
        # find position of new compilation (compilations_count+1)
        compilations_count = len(await RecipeCompilations.get_all(session))

        # Load compilation image to s3
        filename = build_full_path(f"{current_user.username}/compilations/{request.title}", request.image)
        S3Manager.get_instance().send_image_shaped(image=request.image, base_filename=filename)

        new_compilation = await RecipeCompilations.create(
            name=request.title,
            image=filename,
            position=compilations_count+1,
            recipes=recipes_list
        )
        session.add(new_compilation)
    return DefaultResponse(detail="Подборка добавлена")


async def update_recipes_compilation_view(
        current_user: UserModel,
        request: UpdateCompilationRequestModel,
        session: AsyncSession):
    """
    View that updates recipe compilation.
    Description: Compilation is name for a bunch of grouped recipes by admin. Admin should name it and set an image.

    :param current_user: User information object
    :param request: Request with compilation data
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with status
    """
    async with session.begin():
        # First, select all recipes, selected for new compilation
        recipes_list: List[Recipes] = [
            await Recipes.get_by_id(recipe_id, session)
            for recipe_id
            in request.recipe_ids
        ]
        new_image = None
        if request.image:
            # Load compilation image to s3
            filename = build_full_path(f"{current_user.username}/compilations/{request.title}", request.image)
            S3Manager.get_instance().send_image_shaped(image=request.image, base_filename=filename)
            new_image = filename
        await RecipeCompilations.update_by_id(
            session=session,
            compilation_id=request.compilation_id,
            position=request.position,
            name=request.title,
            image=new_image if new_image else None,
            recipes=recipes_list

        )
        await session.commit()
    return DefaultResponse(detail="Подборка обновлена")


async def delete_recipes_compilation_view(
        compilation_id: int,
        session: AsyncSession):
    """
    View that updates recipe compilation.
    Description: Compilation is name for a bunch of grouped recipes by admin. Admin should name it and set an image.

    :param compilation_id: id of compilation
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with status
    """
    async with session.begin():
        # First, select all recipes, selected for new compilation
        await RecipeCompilations.delete(session=session, compilation_id=compilation_id)
        await session.commit()
    return DefaultResponse(detail="Подборка удалена")


async def get_ingredients_view(session: AsyncSession) -> GetIngredientsResponseModel:
    """
    View that returns all ingredients in service.

    :param session: SQLAlchemy AsyncSession object.
    :return: Response with existing ingredients.
    """
    async with (session.begin()):
        stmt = sqlalchemy.select(Ingredients)
        response = await session.execute(stmt)
        loaded_ingredients: List[Ingredients] = response.fetchall()
        if loaded_ingredients:
            output_ingredients: List[IngredientFindResponseModel] = [
                IngredientFindResponseModel(
                    name = ingredient[0].name,
                    ingredient_id = ingredient[0].id
                )
                for ingredient in loaded_ingredients
            ]
        else:
            output_ingredients: List[IngredientFindResponseModel] = []
        return GetIngredientsResponseModel(ingredients=output_ingredients)


async def get_ingredients_with_groups_view(session: AsyncSession) -> GetIngredientsWithGroupsResponseModel:
    """
    View that returns all ingredients in service.

    :param session: SQLAlchemy AsyncSession object.
    :return: Response with existing ingredients.
    """
    async with session.begin():
        stmt = sqlalchemy.select(Ingredients).options(selectinload(Ingredients.groups))
        response = await session.execute(stmt)
        ingredients: List[Ingredients] = response.fetchall()
        if ingredients:
            ingredients = [{"name": i[0].name, "groups":[j.name for j in i[0].groups]} for i in ingredients]
        else:
            ingredients = []
        return GetIngredientsWithGroupsResponseModel(ingredients=ingredients)


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
        current_user: UserModel,
        session: AsyncSession
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
        t = datetime.datetime.now()
        current_user = await Users.get_by_id(session=session, user_id=current_user.id, join_tables=[Users.liked_recipes])
        # Then we need to get recipe object
        t = datetime.datetime.now()
        recipe = await Recipes.get_by_id(recipe_id=recipe.recipe_id, session=session)
        # Now if recipe is not liked, then we should add it to likes
        if recipe not in current_user.liked_recipes:
            t = datetime.datetime.now()
            current_user.liked_recipes.append(recipe)
            return DefaultResponse(detail="Рецепт добавлен в избранное")
        # If recipe already liked, then we should delete it from likes
        else:
            t = datetime.datetime.now()
            current_user.liked_recipes.remove(recipe)
            return DefaultResponse(detail="Рецепт удален из избранного")


async def search_by_field(string_to_find, max_returns, model, field, session, join_tables=()):
    """
    Utility method that search in selected field in selected model for entries. If there are full compare, then
    method will return only fully compared rows, else it will return **max_returns** rows with substring compares.

    :param string_to_find: String for search.
    :param max_returns: Max returns for semi-compared rows.
    :param model: SQLAlchemy model for search.
    :param field: SQLAlchemy model field for search.
    :param join_tables: Tables that should be joined
    :param session: SQLAlchemy AsyncSession object.
    :return: List of found objects.
    """
    search_by_full_compare = sqlalchemy.select(model).where(field == string_to_find).limit(1)
    if join_tables:
        for table in join_tables:
            search_by_full_compare = search_by_full_compare.options(selectinload(table))
    resp = await session.execute(search_by_full_compare)
    resp = resp.scalars().first()
    if resp:
        return [resp]
    else:
        search_by_semi_compare = (
            sqlalchemy.select(model)
            .filter(func.lower(field).like(f"%{string_to_find.lower()}%"))
            .limit(max_returns)
        )
        if join_tables:
            for table in join_tables:
                search_by_semi_compare = search_by_semi_compare.options(selectinload(table))
        resp = await session.execute(search_by_semi_compare)
        resp = resp.scalars().all()
        if resp:
            return resp
        else:
            return []


async def find_all_view(
        string_to_find: str,
        current_user: Optional[UserModel],
        session: AsyncSession,
        max_returns: int = 5,
) -> FindResponseModel:
    """
    Method will search string_to_find in all searchable models: recipes, ingredients, recipe categories. First,
    it returns only fully compared database rows for each model. If fully compared rows not found, then it searches
    semi-compared rows.

    :param string_to_find: String for search.
    :param max_returns: Maximum returned rows for each model.
    :param current_user: User information object.
    :param session: SQLAlchemy AsyncSession object.
    :return: Response with found objects for each model.
    """
    async with session.begin():
        response_model = FindResponseModel(recipes=[], ingredients=[], categories=[])

        # FIND IN RECIPES
        search_recipes: List[Recipes] = await search_by_field(
            string_to_find=string_to_find,
            max_returns=max_returns,
            model=Recipes,
            field=Recipes.title,
            join_tables=[Recipes.allowed_groups],
            session=session)

        search_recipes = list(filter(lambda x: x.image != None, search_recipes))
        if not current_user or PAYED_GROUP_NAME not in current_user.groups:
            search_recipes = list(filter(lambda x: NOT_AUTHENTICATED_GROUP_NAME in [group.name for group in x.allowed_groups], search_recipes))
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
