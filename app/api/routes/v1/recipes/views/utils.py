from typing import List, Optional

import sqlalchemy
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload, lazyload
from starlette import status

from app.utils import S3Manager
from app.api.routes.v1.recipes.utility_classes import CreateRecipeIngredientRequestModel, CreateRecipeStepRequestModel
from app.database.models.base import Ingredients, IngredientsGroups, RecipeDimensions, RecipeIngredients, Recipes, \
    RecipeCategories, RecipeSteps


async def get_ingredients_models(ingredients: CreateRecipeIngredientRequestModel):
    pass


def parse_ingredients_to_pydantic_models(ingredients: str) -> List[CreateRecipeIngredientRequestModel]:
    try:
        ingredients = [CreateRecipeIngredientRequestModel(**i) for i in eval(ingredients)]
        return ingredients
    except ValidationError:
        raise HTTPException(status_code=422, detail="Ошибка в добавлении. "
                                                    "Проверьте правильность введенных ингридиентов")


def parse_steps_to_pydantic_models(steps: str) -> List[CreateRecipeStepRequestModel]:
    try:
        steps = [CreateRecipeStepRequestModel(**i) for i in eval(steps)]
        return steps
    except ValidationError:
        raise HTTPException(status_code=422, detail="Ошибка в добавлении. "
                                                    "Проверьте правильность введенных шагов")


def parse_categories_to_list(categories: str) -> List[str]:
    categories = eval(categories)
    return categories


async def get_ingredient_group_or_create_if_not_exists(name: str, session):
    stmt = sqlalchemy.select(IngredientsGroups).where(IngredientsGroups.name == name)
    response = await session.execute(stmt)
    found_group = response.scalars().first()
    if found_group:
        return found_group
    else:
        new_group = IngredientsGroups(name=name)
        session.add(new_group)
        return new_group


async def get_ingredient_model_or_create_if_not_exists(ingredient: CreateRecipeIngredientRequestModel, session):
    stmt = sqlalchemy.select(Ingredients).where(Ingredients.name == ingredient.name)
    response = await session.execute(stmt)
    found_ingredient = response.scalars().first()
    if found_ingredient:
        return found_ingredient
    new_ingredient_model = Ingredients(name=ingredient.name.lower().capitalize())
    for group in ingredient.groups:
        group_model = await get_ingredient_group_or_create_if_not_exists(group, session)
        new_ingredient_model.groups.append(group_model)
    session.add(new_ingredient_model)
    return new_ingredient_model


async def get_dimension_model_or_create_if_not_exists(dimension: str, session):
    stmt = sqlalchemy.select(RecipeDimensions).where(RecipeDimensions.name == dimension)
    response = await session.execute(stmt)
    found_dimension = response.scalars().first()
    if found_dimension:
        return found_dimension
    else:
        found_dimension = RecipeDimensions(name=dimension)
        session.add(found_dimension)
        return found_dimension


async def create_recipe_ingredient(ingredient: CreateRecipeIngredientRequestModel, session) -> RecipeIngredients:
    ingredient_model = await get_ingredient_model_or_create_if_not_exists(ingredient, session)
    dimension_model = await get_dimension_model_or_create_if_not_exists(ingredient.dimension, session)
    recipe_ingredient = RecipeIngredients(
        ingredient=ingredient_model,
        value=ingredient.weight,
        dimension=dimension_model,
    )
    return recipe_ingredient


async def get_category_or_create_if_not_exists(category: str, session):
    stmt = sqlalchemy.select(RecipeCategories).where(RecipeCategories.name == category)
    response = await session.execute(stmt)
    found_category = response.scalars().first()
    if found_category:
        return found_category
    else:
        found_category = RecipeCategories(name=category)
        return found_category


async def create_or_update_recipe_ingredients(new_ingredients: List[CreateRecipeIngredientRequestModel],
                                              recipe: Recipes, session):
    old_ingredients = recipe.ingredients
    for ingredient in range(len(old_ingredients)):
        old_ingredient = recipe.ingredients.pop()
        await session.delete(old_ingredient)
    for ingredient in new_ingredients:
        new_ingredient = await create_recipe_ingredient(ingredient, session)
        new_ingredient.recipe_id = recipe.id
        recipe.ingredients.append(new_ingredient)


async def remove_deleted_ingredients_from_recipe(
        new_ingredients: List[CreateRecipeIngredientRequestModel],
        recipe: Recipes):
    current_ingredient_names: List[str] = [
        recipe_ingredient.ingredient.name
        for recipe_ingredient
        in recipe.ingredients
    ]
    new_ingredients_names: List[str] = [ingredient.name for ingredient in new_ingredients]
    deleted_ingredient_names = list(set(current_ingredient_names) - set(new_ingredients_names))
    deleted_ingredient_models = list(
        filter(lambda x: x.ingredient.name in deleted_ingredient_names, recipe.ingredients))
    for deleted_ingredient in deleted_ingredient_models:
        recipe.ingredients.remove(deleted_ingredient)


async def update_recipe_steps(
        new_steps: List[CreateRecipeStepRequestModel],
        recipe: Recipes,
        session: AsyncSession
) -> None:
    new_steps = sorted(new_steps, key=lambda x: x.step_num)
    # delete old steps
    for step_num in range(len(recipe.steps)):
        deleted_step = recipe.steps.pop()
        await session.delete(deleted_step)
    for step in new_steps:
        recipe.steps.append(RecipeSteps(step_num=step.step_num, content=step.content))


async def update_recipe_categories(
        new_categories: List[str],
        recipe: Recipes,
        session
):
    current_categories = [i.name for i in recipe.categories]
    categories_to_delete: List[str] = list(set(current_categories) - set(new_categories))
    categories_to_add: List[str] = list(set(new_categories) - set(current_categories))
    for category_num in range(len(categories_to_delete)):
        recipe.categories.remove(
            list(
                filter(
                    lambda x: x.name == categories_to_delete[category_num],
                    recipe.categories)
            )[0]
        )
    for new_category in categories_to_add:
        recipe.categories.append(await get_category_or_create_if_not_exists(new_category, session=session))


async def get_recipe_by_id(recipe_id: int, session: AsyncSession) -> Recipes:
    stmt = ( # TODO: Вынести в отдельную функцию
        sqlalchemy.select(Recipes)
            .where(Recipes.id == recipe_id)
            .limit(1)
            .options(selectinload("*"),)
    )
    resp = await session.execute(stmt)
    recipe: Recipes = resp.scalars().first()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рецепт не найден")
    return recipe


async def get_category_image(category: str, session: AsyncSession) -> Optional[str]:
    stmt = ( # TODO: Вынести в отдельную функцию
        sqlalchemy.select(RecipeCategories)
            .where(RecipeCategories.name == category)
            .limit(1)
            .options(selectinload("*"),)
    )
    resp = await session.execute(stmt)
    category: RecipeCategories = resp.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    for recipe in category.recipes:
        if recipe.image:
            return S3Manager.get_instance().get_url(recipe.image)
    return None
