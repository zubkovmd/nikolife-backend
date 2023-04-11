"""Utils for recipe views"""
from typing import List, Optional

import sqlalchemy
from fastapi import HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from app.api.routes.v1.groups.utils import get_group_model_or_create_if_not_exists
from app.api.routes.v1.utils.service_models import UserModel
from app.api.routes.v1.utils.utility import build_full_path
from app.constants import ADMIN_GROUP_NAME, PAYED_GROUP_NAME, NOT_AUTHENTICATED_GROUP_NAME
from app.utils import S3Manager
from app.api.routes.v1.recipes.utility_classes import (
    CreateRecipeIngredientRequestModel,
    CreateRecipeStepRequestModel,
    RecipeIngredientResponseModel,
    GetRecipesRecipeResponseModel)
from app.database.models.base import (
    Ingredients,
    RecipeIngredients,
    Recipes,
    RecipeCategories,
    RecipeSteps,
    Users,
    Groups,
    RecipeCompilations)


async def create_or_update_recipe_ingredients(
        new_ingredients: List[CreateRecipeIngredientRequestModel],
        recipe: Recipes,
        session
) -> None:
    """
    Method will set new ingredients list for passed recipe.
    For additional info check app.database.models.base -> RecipeIngredients.

    :param new_ingredients: New ingredients list.
    :param recipe: Recipe that should be modified.
    :param session: SQLAlchemy AsyncSession object.
    :return: None
    """
    old_ingredients = recipe.ingredients
    for ingredient in range(len(old_ingredients)):
        old_ingredient = recipe.ingredients.pop()
        await session.delete(old_ingredient)
    for ingredient in new_ingredients:
        new_ingredient = await RecipeIngredients.create(ingredient, session)
        new_ingredient.recipe_id = recipe.id
        recipe.ingredients.append(new_ingredient)


async def update_recipe_steps(
        new_steps: List[CreateRecipeStepRequestModel],
        recipe: Recipes,
        session: AsyncSession
) -> None:
    """
    Method updates passed recipe categories.
    For additional info check app.database.models.base -> RecipeSteps.

    :param new_steps: New recipe steps models list (model contains step number and step text).
    :param recipe: Recipe that should be updated.
    :param session: SQLAlchemy AsyncSession object.
    :return: None
    """
    new_steps = sorted(new_steps, key=lambda x: x.step_num)
    # delete old steps
    for step_num in range(len(recipe.steps)):
        deleted_step = recipe.steps.pop()
        await session.delete(deleted_step)
    # add new steps
    for step in new_steps:
        recipe.steps.append(RecipeSteps(step_num=step.step_num, content=step.content))


async def update_recipe_categories(
        new_categories: List[str],
        recipe: Recipes,
        session
) -> None:
    """
    Method updates passed recipe categories.
    For additional info check app.database.models.base -> RecipeCategories.

    :param new_categories: New categories list.
    :param recipe: Recipe that should be updated.
    :param session: SQLAlchemy AsyncSession object.
    :return: None
    """
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
        recipe.categories.append(await RecipeCategories.get_by_name_or_create(category=new_category, session=session))


async def update_recipe_groups(
        new_groups: List[str],
        recipe: Recipes,
        session: AsyncSession
) -> None:
    """
    Method updates allowed user groups for recipe

    :param new_groups: new group names list
    :param recipe: Recipe that should be updated
    :param session: SQLAlchemy AsyncSession object
    :return: None
    """
    group_models: List[Groups] = []
    for group in new_groups:
        group_model = await get_group_model_or_create_if_not_exists(group, session)
        if group_model:
            group_models.append(group_model)
    recipe.allowed_groups = group_models


async def get_recipe_by_id(recipe_id: int, session: AsyncSession) -> Recipes:
    """
    Method search recipe by passed id. If recipe not found, then it throws
    404_NOT_FOUND exception

    :param recipe_id: id of recipe.
    :param session: SQLAlchemy AsyncSession object.
    :return: Found recipe.
    """
    stmt = (
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


async def check_is_user_allow_to_modify_recipe(recipe: Recipes, current_user: UserModel, session: AsyncSession):
    """
    Method checks is user allowed to modify recipe. Allowed if this user is admin or it user created recipe.
    If user allowed, then method will work silently, else if user not allowed, then it throws
    401_UNAUTHORIZED exception.

    :param recipe: Recipe object.
    :param current_user: User information object.
    :return: None
    """
    recipe_created_by_this_user = recipe.user.id == current_user.id
    user: Users = await Users.get_by_id(user_id=current_user.id, session=session, join_tables=[Users.groups])
    user_is_admin = ADMIN_GROUP_NAME in [group.name for group in user.groups]
    # if user is not admin and try to delete recipe that was added by other user, then we should throw 401
    if not recipe_created_by_this_user and not user_is_admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="У вас нет прав на удаление рецепта")


async def select_recipes_and_filter_them(
        session: AsyncSession,
        user_groups: list[str],
        include_categories: Optional[list[str]] = None,
        prefer_ingredients: Optional[list[str]] = None,
        compilation: Optional[list[str]] = None,
        exclude_groups: Optional[list[str]] = None
) -> List[Recipes]:
    """
    Method selects all recipes with filters.

    :param session: SQLAlchemy AsyncSession object
    :param user_groups: Requested user groups. Method filters recipes where user groups intersect with
    recipe allowed groups
    :param include_categories: If passed, filter recipes where categories intersect with these
    :param prefer_ingredients: If passed, filter recipes where ingredients intersect with these
    :param compilation: If passed, filter recipes that selected for this compilation
    :param exclude_groups: If passed, filter recipes where groups do not intersect with these
    :return:
    """
    # First make base query
    stmt = (
        select(Recipes)
        .options(selectinload(Recipes.allowed_groups))
        .options(selectinload(Recipes.liked_by))
    )
    if PAYED_GROUP_NAME not in user_groups and ADMIN_GROUP_NAME not in user_groups:
        stmt = stmt.filter(Recipes.allowed_groups.any(Groups.name.notlike(PAYED_GROUP_NAME)))
        pass

    if ADMIN_GROUP_NAME not in user_groups:
        stmt = stmt.where(Recipes.image.isnot(None))  # some recipes do not have images, so filter them

    # If include_categories passed, then filter recipes where categories intersect at least with one of these
    if include_categories:
        stmt = stmt.options(selectinload(Recipes.categories))
        stmt = stmt.filter(Recipes.categories.any(RecipeCategories.name.in_(include_categories)))

    if prefer_ingredients or exclude_groups:
        # this two filters refers to one table - RecipeIngredients, so we need join it when one of these passed
        stmt = stmt.join(RecipeIngredients).join(Ingredients)
        # if prefer_ingredients passed, then we should filter recipes where prefer_ingredients intersect with at least
        # one ingredient name
        if prefer_ingredients:
            stmt = stmt.filter(Ingredients.name.in_(prefer_ingredients))

        # if exclude_groups passed, then we should filter recipes where groups do not intersect with any of
        # excluded groups
        # if exclude_groups:  # TODO: not working at this time, need to fix it.
        #     stmt = stmt.join(association_ingredients_groups).join(IngredientsGroups)
        #     stmt = stmt.filter(IngredientsGroups.name.notin_(exclude_groups))
    # if compilation passed, then we should select recipes that selected for this compilation
    if compilation:
        stmt = stmt.options(selectinload(Recipes.compilations))
        stmt = stmt.filter(Recipes.compilations.any(RecipeCompilations.name.in_([compilation])))
    response = await session.execute(stmt)
    recipes: List[Recipes] = response.scalars().all()
    return recipes


def build_recipes_output(recipes: list[Recipes], current_user: Optional[UserModel]) -> List[GetRecipesRecipeResponseModel]:
    """
    Method build list of recipes to output format. Add links to images and liked fields.
    Description: recipe 'liked' if user who request this recipe is liked it.

    :param recipes: List of recipes.
    :param current_user: User information object
    :return: List of formatted recipes
    """
    user_groups = current_user.groups if current_user else [NOT_AUTHENTICATED_GROUP_NAME]
    if ADMIN_GROUP_NAME not in user_groups:
        recipes = list(filter(lambda x: x.image is not None, recipes))

    if PAYED_GROUP_NAME not in user_groups or ADMIN_GROUP_NAME not in user_groups:
        recipes = list(filter(lambda x: PAYED_GROUP_NAME not in x.allowed_groups, recipes))

    recipes_to_return = []
    for recipe in recipes:
        recipe_dicted = recipe.__dict__
        if recipe.image:
            image = S3Manager.get_instance().get_url(f"{recipe.image}_small.jpg")
        else:
            image = None
        recipe_dicted["image"] = image
        recipe_dicted["liked"] = current_user in recipe.liked_by if current_user else False
        recipe_dicted["allowed"] = True if any((True for user_group in (current_user.groups if current_user else ["no_auth"]) if (user_group.name if user_group is not "no_auth" else "no_auth") in [group.name for group in recipe.allowed_groups])) else False
        recipe_dicted["allowed_groups_list"] = [group.name for group in recipe.allowed_groups]
        recipes_to_return.append(GetRecipesRecipeResponseModel(**recipe_dicted))
    return sorted(recipes_to_return, key=lambda x: x.allowed, reverse=True)


async def select_liked_recipes(
        session: AsyncSession,
        current_user: UserModel
) -> List[Recipes]:
    """
    Method selects all recipes what was liked by user.

    :param session: SQLAlchemy AsyncSession
    :param current_user: User information object
    :return: recipes list
    """
    stmt = (
        select(Recipes)
        .where(Recipes.user_id == 1, Recipes.image.isnot(None))  # some recipes do not have images, so filter them
        .filter(Recipes.allowed_groups.any(Groups.name.in_([group for group in current_user.groups])))
        .options(selectinload('*'))
    )
    stmt = stmt.filter(Recipes.liked_by.any(Users.id.in_([current_user.id])))
    response = await session.execute(stmt)
    recipes: List[Recipes] = response.scalars().all()
    return recipes


def build_recipe_output(recipe: Recipes, current_user: UserModel) -> dict:
    """
    Method build recipe to output format. Add links to images and liked fields.
    Description: recipe 'liked' if user who request this recipe is liked it.

    :param recipe: recipe.
    :param current_user: User information object
    :return: Formatted recipe
    """
    recipe_response = dict(recipe.__dict__)
    recipe_response["ingredients"] = [
        RecipeIngredientResponseModel(name=i.ingredient.name, value=i.value, dimension=i.dimension.name, groups=[j.name for j in i.ingredient.groups]) for i
        in
        recipe_response["ingredients"]]
    recipe_response["steps"] = [i.content for i in
                                list(sorted(recipe_response["steps"], key=lambda x: x.step_num))]
    recipe_response["categories"] = [i.name for i in recipe_response["categories"]]
    recipe_response["image"] = None if recipe_response["image"] is None else S3Manager.get_instance().get_url(
        f"{recipe_response['image']}_med.jpg")
    recipe_response["allowed_groups"] = [group.name for group in recipe_response["allowed_groups"]]
    recipe_response["liked"] = current_user.username in [user.username for user in recipe.liked_by] if current_user else False
    return recipe_response


async def create_new_recipe(
        title: str,
        image: UploadFile,
        time: int,
        complexity: str,
        servings: int,
        categories: List[str],
        steps: List[CreateRecipeStepRequestModel],
        ingredients: List[CreateRecipeIngredientRequestModel],
        allowed_groups: Optional[List[str]],
        session: AsyncSession,
        current_user: UserModel,
) -> int:
    """
    Method creates new recipe vis passed data

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
    :return:
    """
    # creates default recipe without additional data
    new_recipe: Recipes = Recipes(title=title, time=time, complexity=complexity, servings=servings,
                                  user_id=current_user.id)
    # adding ingredients to recipe. if ingredient don't exist, first create new ingredient
    for ingredient in ingredients:
        new_recipe.ingredients.append(await RecipeIngredients.create(ingredient, session))
    # adding cooking steps to recipe.
    for step in steps:
        new_recipe.steps.append(RecipeSteps(step_num=step.step_num, content=step.content))
    # adding categories to recipe. if ingredient don't exist, first create new ingredient
    for category in categories:
        new_recipe.categories.append(await RecipeCategories.get_by_name_or_create(category, session))

    if allowed_groups:
        group_models = []
        for group in allowed_groups:
            group_models.append(await get_group_model_or_create_if_not_exists(group, session))
        new_recipe.allowed_groups = group_models

    if image:
        filename = build_full_path(f"{current_user.username}/recipes/{new_recipe.title}", image)
        S3Manager.get_instance().send_image_shaped(image=image, base_filename=filename)
        new_recipe.image = filename
    session.add(new_recipe)
    await session.flush()
    return new_recipe.id


async def update_recipe(
        recipe: Recipes,
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
) -> None:
    """
    Method updates recipe with new data. If user who try to update recipe is not recipe creator and not admin,
    then throws 401_UNAUTHORIZED exception

    :param recipe: Recipe object
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
    :return: None
    """
    await check_is_user_allow_to_modify_recipe(recipe=recipe, current_user=current_user, session=session)
    if title:
        recipe.title = title
    if image:
        filename = build_full_path(f"{current_user.username}/recipes/{recipe.title}", image)
        S3Manager.get_instance().send_image_shaped(image=image, base_filename=filename)
        recipe.image = filename
    if time:
        recipe.time = time
    if complexity:
        recipe.complexity = complexity
    if servings:
        recipe.servings = servings
    if ingredients:
        ingredients_parsed: List[CreateRecipeIngredientRequestModel] = parse_ingredients_to_pydantic_models(
            ingredients=ingredients)
        await create_or_update_recipe_ingredients(new_ingredients=ingredients_parsed, recipe=recipe, session=session)

    if steps:
        steps: List[CreateRecipeStepRequestModel] = parse_steps_to_pydantic_models(steps=steps)
        await update_recipe_steps(new_steps=steps, recipe=recipe, session=session)

    if categories:
        categories = parse_categories_to_list(categories)
        await update_recipe_categories(new_categories=categories, recipe=recipe, session=session)

    if allowed_groups:
        allowed_groups = eval(allowed_groups)
        await update_recipe_groups(allowed_groups, recipe=recipe, session=session)


async def get_category_image(category: str, session: AsyncSession) -> Optional[str]:
    """
    Method returns image of first recipe in category that has image.

    :param category: category name
    :param session: SQLALchemy AsyncSession object
    :return: Category image if any recipe with image found, else None
    """
    stmt = (
        sqlalchemy.select(RecipeCategories)
        .where(RecipeCategories.name == category)
        .limit(1)
        .options(selectinload(RecipeCategories.recipes))
    )
    resp = await session.execute(stmt)
    category: RecipeCategories = resp.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    if category.image:
        return S3Manager.get_instance().get_url(f"{category.image}_small.jpg")
    for recipe in category.recipes:
        if recipe.image:
            return S3Manager.get_instance().get_url(f"{recipe.image}_small.jpg")
    return None


def parse_ingredients_to_pydantic_models(ingredients: str) -> List[CreateRecipeIngredientRequestModel]:
    """
    Parses jsoned list of ingredients to pydantic models.

    :param ingredients: Jsoned list of ingredients.
    :return: Parsed ingredients.
    """
    try:
        ingredients = [CreateRecipeIngredientRequestModel(**i) for i in eval(ingredients)]
        return ingredients
    except ValidationError:
        raise HTTPException(status_code=422, detail="Ошибка в добавлении. "
                                                    "Проверьте правильность введенных ингридиентов")


def parse_steps_to_pydantic_models(steps: str) -> List[CreateRecipeStepRequestModel]:
    """
    Parses jsoned list of ingredients to pydantic models.

    :param steps: Jsoned list of steps.
    :return: Parsed ingredients.
    """
    try:
        steps = [CreateRecipeStepRequestModel(**i) for i in eval(steps)]
        return steps
    except ValidationError:
        raise HTTPException(status_code=422, detail="Ошибка в добавлении. "
                                                    "Проверьте правильность введенных шагов")


def parse_categories_to_list(categories: str) -> List[str]:
    """
    Parses jsoned list of ingredients to python list.

    :param categories: Jsoned list of categories.
    :return: Parsed ingredients.
    """
    categories = eval(categories)
    return categories
