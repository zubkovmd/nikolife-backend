from datetime import datetime
from typing import List, Optional

import sqlalchemy
from fastapi import Depends, HTTPException, Response, Form, UploadFile, File
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, lazyload, selectinload
from starlette import status

from app.api.routes.default_response_models import DefaultResponse, DefaultResponseWithPayload
from app.api.routes.v1.recipes.utility_classes import GetRecipesRecipeResponseModel, RecipeIngredientResponseModel, \
    CreateRecipeIngredientRequestModel, CreateRecipeStepRequestModel, GetRecipesRequestModel
from app.api.routes.v1.recipes.views.utils import parse_ingredients_to_pydantic_models, parse_steps_to_pydantic_models, \
    create_recipe_ingredient, get_category_or_create_if_not_exists, create_or_update_recipe_ingredients, \
    remove_deleted_ingredients_from_recipe, update_recipe_steps, update_recipe_categories, parse_categories_to_list, \
    get_recipe_by_id
from app.api.routes.v1.users.utils import get_user_by_id
from app.api.routes.v1.utils.auth import get_user_by_token
from app.api.routes.v1.utils.service_models import UserModel
from app.constants import ADMIN_GROUP_NAME
from app.database import DatabaseManagerAsync
from app.database.models.base import Users, Recipes, Ingredients, RecipeDimensions, RecipeIngredients, \
    IngredientsGroups, RecipeSteps, RecipeCategories, Groups, association_recipes_categories, \
    association_ingredients_groups, RecipeCompilations
from app.utils import S3Manager
from app.log import default_logger


async def get_recipes_view(
        # recipes_request: Optional[GetRecipesRequestModel],
        prefer_ingredients: Optional[List[str]],
        exclude_groups: Optional[List[str]],
        include_categories: Optional[List[str]],
        compilation: Optional[str],
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token),):
    async with session.begin():
        stmt = (
            select(Users)
            .filter(Users.id == current_user.id)  # TODO: Вынести в отдельную функцию
            .options(
                selectinload(Users.groups),
            )
        )
        resp = await session.execute(stmt)
        current_user: Users = resp.scalars().first()
        default_logger.info(f"got /get_recipes from {repr(current_user)}")
        stmt = (
            select(Recipes)
            .where(Recipes.image.isnot(None))  # TODO: УБРАТЬ ФИЛЬТР БЕЗ КАРТИНОК, ВЫНЕСТИ В ФУНКЦИЮ
            .filter(Recipes.allowed_groups.any(Groups.id.in_([i.id for i in current_user.groups])))
            .options(selectinload(
                '*'
            ),)
        )
        if include_categories:
            stmt = stmt.filter(Recipes.categories.any(RecipeCategories.name.in_(include_categories)))
        if prefer_ingredients or exclude_groups:
            stmt = stmt.join(RecipeIngredients).join(Ingredients)
            if prefer_ingredients:
                stmt = stmt.filter(Ingredients.name.in_(prefer_ingredients))
            # if exclude_groups:  # TODO: пофиксить
            #     stmt = stmt.join(association_ingredients_groups).join(IngredientsGroups)
            #     stmt = stmt.filter(IngredientsGroups.name.notin_(exclude_groups))
                # stmt = stmt.filter(sqlalchemy.not_(Ingredients.groups.any(IngredientsGroups.name.in_(a[:2]))))
        if compilation:
            stmt = stmt.filter(Recipes.compilations.any(RecipeCompilations.name.in_([compilation])))
        response = await session.execute(stmt)
        recipes: List[Recipes] = response.scalars().all()
        if not recipes:
            return {"recipes": []}
        recipes_to_return = []
        for recipe in recipes:
            if exclude_groups:  # TODO: пофиксить селект выше, убрать это
                ingredient_groups_lists = [ingredient.ingredient.groups for ingredient in recipe.ingredients]
                if len(set(exclude_groups).intersection(set([j.name for sub in ingredient_groups_lists for j in sub]))) > 0:
                    continue
            recipe_dicted = recipe.__dict__
            if recipe.image:
                image = S3Manager.get_instance().get_url(recipe.image)
            else:
                image = None
            recipe_dicted["image"] = image
            recipe_dicted["liked"] = current_user in recipe.liked_by
            recipes_to_return.append(GetRecipesRecipeResponseModel(**recipe_dicted))
        return {"recipes": recipes_to_return}


async def get_recipes_by_ingredient_view(
        ingredient_name: str,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token),
):
    stmt = (  # TODO: Вынести в отдельную функцию
        select(Users)
            .filter(Users.id == current_user.id)
            .options(
            selectinload(Users.groups),
        )
    )
    resp = await session.execute(stmt)
    current_user: Users = resp.scalars().first()
    default_logger.info(f"got /get_recipes from {repr(current_user)}")
    stmt = (  # TODO: Вынести в отдельную функцию
        select(Recipes)
            .where(Recipes.user_id == 1, Recipes.image.isnot(None))  # TODO: УБРАТЬ ФИЛЬТР БЕЗ КАРТИНОК, ВЫНЕСТИ В ФУНКЦИЮ
            .filter(Recipes.allowed_groups.any(Groups.id.in_([i.id for i in current_user.groups])))
            .options(selectinload(
            '*'
        ), )
    )
    stmt = stmt.join(RecipeIngredients).join(Ingredients).filter(Ingredients.name.in_([ingredient_name]))
    response = await session.execute(stmt)
    recipes: List[Recipes] = response.scalars().all()
    if not recipes:
        return {"recipes": []}
    recipes_to_return = []
    for recipe in recipes:
        recipe_dicted = recipe.__dict__
        if recipe.image:
            image = S3Manager.get_instance().get_url(recipe.image)
        else:
            image = None
        recipe_dicted["image"] = image
        recipe_dicted["liked"] = current_user in recipe.liked_by
        recipes_to_return.append(GetRecipesRecipeResponseModel(**recipe_dicted))
    return {"recipes": recipes_to_return}


async def get_recipes_by_category_view(
        category_name: str,
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token),
):
    stmt = (  # TODO: Вынести в отдельную функцию
        select(Users)
            .filter(Users.id == current_user.id)
            .options(
            selectinload(Users.groups),
        )
    )
    resp = await session.execute(stmt)
    current_user: Users = resp.scalars().first()
    default_logger.info(f"got /get_recipes from {repr(current_user)}")
    stmt = (
        select(Recipes)
            .where(Recipes.user_id == 1, Recipes.image.isnot(None))  # TODO: УБРАТЬ ФИЛЬТР БЕЗ КАРТИНОК, ВЫНЕСТИ В ФУНКЦИЮ
            .filter(Recipes.allowed_groups.any(Groups.id.in_([i.id for i in current_user.groups])))
            .join(association_recipes_categories)
            .join(RecipeCategories)
            .filter(RecipeCategories.name.in_([category_name]))
            .options(selectinload(
            '*'
        ), )
    )
    response = await session.execute(stmt)
    recipes: List[Recipes] = response.scalars().all()
    if not recipes:
        return {"recipes": []}
    recipes_to_return = []
    for recipe in recipes:
        recipe_dicted = recipe.__dict__
        if recipe.image:
            image = S3Manager.get_instance().get_url(recipe.image)
        else:
            image = None
        recipe_dicted["image"] = image
        recipe_dicted["liked"] = current_user in recipe.liked_by
        recipes_to_return.append(GetRecipesRecipeResponseModel(**recipe_dicted))
    return {"recipes": recipes_to_return}


async def get_liked_recipes_view(
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token)):
    async with session.begin():
        stmt = (  # TODO: Вынести в отдельную функцию
            select(Users)
            .filter(Users.id == current_user.id)
            .options(
                selectinload(Users.groups),
            )
        )
        resp = await session.execute(stmt)
        current_user: Users = resp.scalars().first()
        default_logger.info(f"got /get_recipes from {repr(current_user)}")
        stmt = (
            select(Recipes)
            .where(Recipes.user_id == 1, Recipes.image.isnot(None))  # TODO: УБРАТЬ ФИЛЬТР БЕЗ КАРТИНОК, ВЫНЕСТИ В ФУНКЦИЮ
            .options(selectinload(
                '*'
            ),)
        )
        response = await session.execute(stmt)
        recipes: List[Recipes] = response.scalars().all()
        if not recipes:
            return {"recipes": []}
        recipes_to_return = []
        for recipe in recipes:
            if not current_user in recipe.liked_by:
                continue
            if len(set(group.name for group in current_user.groups).intersection(set(i.name for i in recipe.allowed_groups))) == 0:
                continue
            recipe_dicted = recipe.__dict__
            if recipe.image:
                image = S3Manager.get_instance().get_url(recipe.image)
            else:
                image = None
            recipe_dicted["image"] = image
            recipe_dicted["liked"] = current_user in recipe.liked_by
            recipes_to_return.append(GetRecipesRecipeResponseModel(**recipe_dicted))
        return {"recipes": recipes_to_return}


async def get_recipe_view(
        recipe_id: int,
        session: AsyncSession,
        current_user: Users,
):
    async with session.begin():
        # current_user: Users = await get_user_by_id(user_id=current_user.id, session=session)
        # recipe: Recipes = await get_recipe_by_id(recipe_id=recipe_id, session=session)
        stmt = (  # TODO: Вынести в отдельную функцию
            select(Recipes)
                .filter(Recipes.id == recipe_id)
                .options(
                    selectinload(Recipes.ingredients).subqueryload(RecipeIngredients.ingredient),
                    selectinload(Recipes.ingredients).subqueryload(RecipeIngredients.dimension),
                    selectinload(Recipes.steps),
                    selectinload(Recipes.categories),
                    selectinload(Recipes.liked_by),
                    selectinload(Recipes.allowed_groups)
                )
        )
        response = await session.execute(stmt)
        recipe: Recipes = response.scalars().first()
        stmt = (  # TODO: Вынести в отдельную функцию
            select(Users)
            .filter(Users.id == current_user.id)
            .options(
                selectinload(Users.groups)
            )
        )
        response = await session.execute(stmt)
        current_user: Users = response.scalars().first()

        if len(set(group.name for group in current_user.groups).intersection(set(i.name for i in recipe.allowed_groups))) == 0:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="У вас нет досутпа к этому рецепту")
        if not recipe:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рецепт не найден")
        recipe_response = dict(recipe.__dict__)
        recipe_response["ingredients"] = [
            RecipeIngredientResponseModel(name=i.ingredient.name, value=i.value, dimension=i.dimension.name) for i in
            recipe_response["ingredients"]]
        recipe_response["steps"] = [i.content for i in list(sorted(recipe_response["steps"], key=lambda x: x.step_num))]
        recipe_response["categories"] = [i.name for i in recipe_response["categories"]]
        recipe_response["image"] = None if recipe_response["image"] is None else S3Manager.get_instance().get_url(
            recipe_response["image"])
        recipe_response["liked"] = current_user in recipe.liked_by
        return recipe_response


async def delete_recipe_view(response: Response, recipe_id: int, session: AsyncSession, current_user):
    async with session.begin():
        recipe: Recipes = await get_recipe_by_id(recipe_id=recipe_id, session=session)
        user_created_recipe = recipe.user
        user_groups = user_created_recipe.groups
        if not user_created_recipe.id == current_user.id and ADMIN_GROUP_NAME not in user_groups:
            response.status_code = status.HTTP_403_FORBIDDEN
            return DefaultResponse(detail="У вас нет прав на удаление этого рецепта")
        await session.delete(recipe)
        return DefaultResponse(detail="Рецепт был удален")


async def create_recipe_view(
        response: Response,
        title: str = Form(),
        image: UploadFile = File(default=None),
        time: int = Form(),
        complexity: str = Form(),
        servings: int = Form(),
        categories: str = Form(),
        steps: str = Form(),
        ingredients: str = Form(),
        session: AsyncSession = Depends(DatabaseManagerAsync.get_instance().get_session_object),
        current_user: UserModel = Depends(get_user_by_token),
):
    ingredients: List[CreateRecipeIngredientRequestModel] = parse_ingredients_to_pydantic_models(ingredients=ingredients)
    steps: List[CreateRecipeStepRequestModel] = parse_steps_to_pydantic_models(steps=steps)
    categories = parse_categories_to_list(categories)
    async with session.begin():
        new_recipe: Recipes = Recipes(title=title, time=time, complexity=complexity, servings=servings,
                                      user_id=current_user.id)
        # recipe ingredients
        for ingredient in ingredients:
            new_recipe.ingredients.append(await create_recipe_ingredient(ingredient, session))
        # steps
        for step in steps:
            new_recipe.steps.append(RecipeSteps(step_num=step.step_num, content=step.content))
        # categories
        for category in categories:
            new_recipe.categories.append(await get_category_or_create_if_not_exists(category, session))
        filename = f"/{current_user.username}/recipes/{new_recipe.title}_{int(datetime.now().timestamp())}.jpg"
        S3Manager.get_instance().send_memory_file_to_s3(image.file, filename)
        new_recipe.image = filename
        session.add(new_recipe)
        await session.flush()
        return DefaultResponseWithPayload(detail="Рецепт успешно добавлен", payload={"recipe_id": new_recipe.id})


async def update_recipe_view(
    response: Response,
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
    async with session.begin():
        recipe = await get_recipe_by_id(recipe_id=recipe_id, session=session)
        if title:
            recipe.title = title
        if image:
            filename = f"/{current_user.username}/recipes/{recipe.title}_{int(datetime.now().timestamp())}.jpg"
            S3Manager.get_instance().send_memory_file_to_s3(image.file, filename)
            recipe.image = filename
        if time:
            recipe.time = time
        if complexity:
            recipe.complexity = complexity
        if servings:
            recipe.servings = servings

        if ingredients:
            ingredients: List[CreateRecipeIngredientRequestModel] = parse_ingredients_to_pydantic_models(
                ingredients=ingredients)
            # await remove_deleted_ingredients_from_recipe(ingredients, recipe)
            await create_or_update_recipe_ingredients(new_ingredients=ingredients, recipe=recipe, session=session)

        if steps:
            steps: List[CreateRecipeStepRequestModel] = parse_steps_to_pydantic_models(steps=steps)
            await update_recipe_steps(new_steps=steps, recipe=recipe, session=session)

        if categories:
            categories = parse_categories_to_list(categories)
            await update_recipe_categories(new_categories=categories, recipe=recipe, session=session)

        return DefaultResponse(detail="Рецепт обновлен")

