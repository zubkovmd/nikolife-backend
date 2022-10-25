from typing import List

import sqlalchemy
from fastapi import Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from starlette import status
from sqlalchemy_searchable import search

from app.api.routes.default_responses import DefaultResponse
from app.api.routes.v1.recipes.utility_classes import RecipeLikesRequestModel, FindRequestModel, FindResponseModel, \
    RecipeFindResponseModel, IngredientFindResponseModel, CategoryFindResponseModel, CreateCompilationRequestModel
from app.api.routes.v1.recipes.views.utils import get_recipe_by_id, get_category_image
from app.api.routes.v1.users.utils import get_user_by_id
from app.api.routes.v1.users.views.utils import get_user_model
from app.api.routes.v1.utils.auth import get_user_by_token
from app.database.manager import manager
from app.database.models.base import RecipeCategories, Ingredients, RecipeDimensions, IngredientsGroups, Users, Recipes, \
    association_recipes_categories, RecipeCompilations
from app.utils.s3_service import manager as s3_manager


async def get_recipes_categories_view(session: AsyncSession):
    async with session.begin():
        stmt = sqlalchemy.select(RecipeCategories.name)
        response = await session.execute(stmt)
        categories = response.fetchall()
        if categories:
            response = {"categories": []}
            for category in categories:
                image = await get_category_image(category=category[0], session=session)
                if image is None:
                    continue
                response["categories"].append(
                    {
                        "name": category[0],
                        "image": image
                    }
                )
            return response
        else:
            return {"categories": []}


async def get_recipes_compilations_view(session: AsyncSession):
    async with session.begin():
        stmt = sqlalchemy.select(RecipeCompilations)
        response = await session.execute(stmt)
        compilations: List[RecipeCompilations] = response.scalars().all()
        if compilations:
            response = {"compilations": []}
            for compilation in compilations:
                response["compilations"].append(
                    {
                        "name": compilation.name,
                        "image": s3_manager.get_url(compilation.image)
                    }
                )
            return response
        else:
            return {"compilations": []}


async def create_recipes_compilation_view(current_user: Users, request: CreateCompilationRequestModel,session: AsyncSession):
    async with session.begin():
        recipes = (await session.execute(sqlalchemy.select(Recipes).where(Recipes.id.in_(request.recipe_ids)))).scalars().all()
        filename = f"{current_user.username}/compilations/{request.image.filename}"
        s3_manager.send_memory_file_to_s3(request.image.file, filename)
        session.add(RecipeCompilations(name=request.title, recipes=recipes, image=filename))
    return DefaultResponse(detail="Подборка добавлена")


async def get_available_ingredients_view(session: AsyncSession):
    async with session.begin():
        stmt = sqlalchemy.select(Ingredients.name)
        response = await session.execute(stmt)
        ingredients: List[str] = response.fetchall()
        if ingredients:
            ingredients = [i[0] for i in ingredients]
        else:
            ingredients = []
        return {"ingredients": ingredients}


async def get_available_dimensions_view(session: AsyncSession):
    async with session.begin():
        stmt = sqlalchemy.select(RecipeDimensions.name)
        response = await session.execute(stmt)
        dimensions: List[str] = response.fetchall()
        if dimensions:
            dimensions = [i[0] for i in dimensions]
        else:
            dimensions = []
        return {"dimensions": dimensions}


async def get_available_ingredients_groups_view(session: AsyncSession):
    async with session.begin():
        stmt = sqlalchemy.select(IngredientsGroups.name)
        response = await session.execute(stmt)
        groups: List[str] = response.fetchall()
        if groups:
            groups = [i[0] for i in groups]
        else:
            groups = []
        return {"groups": groups}


async def toggle_recipe_like_view(recipe: RecipeLikesRequestModel,
                                  current_user: Users = Depends(get_user_by_token),
                                  session: AsyncSession = Depends(manager.get_session_object)):
    async with session.begin():
        current_user_stmt = select(Users).filter(Users.id == current_user.id).options(selectinload(Users.liked_recipes))
        resp = await session.execute(current_user_stmt)
        current_user: Users = resp.scalars().first()
        recipe = await get_recipe_by_id(recipe_id=recipe.recipe_id, session=session)
        if recipe not in current_user.liked_recipes:
            current_user.liked_recipes.append(recipe)
            return DefaultResponse(detail="Рецепт добавлен в избранное")
        else:
            current_user.liked_recipes.remove(recipe)
            return DefaultResponse(detail="Рецепт удален из избранного")


async def remove_recipe_from_likes_view(recipe: RecipeLikesRequestModel,
                                        current_user: Users = Depends(get_user_by_token),
                                        session: AsyncSession = Depends(manager.get_session_object)):
    async with session.begin():
        current_user = await get_user_model(username=current_user.username, session=session)
        recipe = await get_recipe_by_id(recipe_id=recipe.recipe_id, session=session)
        if recipe.id not in [recipe.id for recipe in current_user.liked_recipes]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рецепт не в избранном")
        current_user.liked_recipes.remove(recipe)
    return DefaultResponse(detail="Рецепт удален из избранного")


async def search_by_field(string_to_find, max_returns, model, field, session):
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

async def find_all_view(string_to_find: str, max_returns: int = 5, session: AsyncSession = Depends(manager.get_session_object)):
    async with session.begin():
        response_model = FindResponseModel(recipes=[], ingredients=[], categories=[])

        # FIND IN RECIPES
        search_recipes: List[Recipes] = await search_by_field(string_to_find=string_to_find, max_returns=max_returns, model=Recipes, field=Recipes.title, session=session)
        response_model.recipes = [RecipeFindResponseModel(title=i.title, recipe_id=i.id) for i in search_recipes]
        # FIND IN CATEGORIES
        searh_categories: List[RecipeCategories] = await search_by_field(string_to_find=string_to_find, max_returns=max_returns, model=RecipeCategories, field=RecipeCategories.name, session=session)
        response_model.categories = [CategoryFindResponseModel(name=category.name, category_id=category.id) for category in searh_categories]
        # FIND IN INGREDIENTS
        searh_ingredients: List[Ingredients] = await search_by_field(string_to_find=string_to_find, max_returns=max_returns, model=Ingredients, field=Ingredients.name, session=session)
        response_model.ingredients = [IngredientFindResponseModel(name=ingredient.name, ingredient_id=ingredient.id) for ingredient in searh_ingredients]

        return response_model
