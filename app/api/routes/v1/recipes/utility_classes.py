from typing import List, Optional

from fastapi import Form, UploadFile
from pydantic import BaseModel


class GetRecipesRequestModel(BaseModel):
    prefer_ingredients: Optional[List[str]]
    exclude_groups: Optional[List[str]]


class CreateRecipeIngredientRequestModel(BaseModel):
    name: str
    weight: float
    dimension: str
    groups: List[str]


class CreateRecipeStepRequestModel(BaseModel):
    step_num: int
    content: str


class CreateRecipeRequestModel(BaseModel):
    title: str = Form()
    time: int = Form()
    complexity: str = Form()
    servings: int = Form()
    categories: List[str] = Form()
    steps: List[CreateRecipeStepRequestModel] = Form(...)
    ingredients: List[CreateRecipeIngredientRequestModel] = Form()


class CreateCompilationRequestModel(BaseModel):
    recipe_ids: List[int]
    title: str
    image: UploadFile


class RecipeLikesRequestModel(BaseModel):
    recipe_id: int


class RecipecategoryResponseModel(BaseModel):
    name: str
    image: str


class RecipeCategoriesResponseModel(BaseModel):
    categories: List[RecipecategoryResponseModel]


class RecipeCompilationResponseModel(BaseModel):
    name: str
    image: str


class RecipeCompilationsResponseModel(BaseModel):
    compilations: List[RecipeCompilationResponseModel]


class RecipeFindResponseModel(BaseModel):
    title: str
    recipe_id: int


class IngredientFindResponseModel(BaseModel):
    name: str
    ingredient_id: int


class CategoryFindResponseModel(BaseModel):
    name: str
    category_id: int


class FindResponseModel(BaseModel):
    recipes: List[RecipeFindResponseModel]
    ingredients: List[IngredientFindResponseModel]
    categories: List[CategoryFindResponseModel]


class FindRequestModel(BaseModel):
    string_to_find: str


class RecipeIngredientResponseModel(BaseModel):
    name: str
    value: float
    dimension: str


class RecipeResponseModel(BaseModel):
    id: int
    title: str
    image: Optional[str]
    time: int
    complexity: str
    ingredients: List[RecipeIngredientResponseModel]
    steps: List[str]
    categories: List[str]
    servings: int
    liked: bool


class GetRecipesResponseModel(BaseModel):
    recipes: List


class GetRecipesRecipeResponseModel(BaseModel):
    id: int
    title: str
    image: Optional[str]
    time: int
    complexity: str
    servings: int
    liked: bool
