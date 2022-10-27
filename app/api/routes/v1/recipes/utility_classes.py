"""Models that uses in recipe requests"""

from typing import List, Optional

from fastapi import Form, UploadFile
from pydantic import BaseModel


class GetRecipesRequestModel(BaseModel):
    """Model for recipe request by preferred ingredients and excluded ingredient groups"""
    prefer_ingredients: Optional[List[str]]
    exclude_groups: Optional[List[str]]


class CreateRecipeIngredientRequestModel(BaseModel):
    """Model for ingredient creation"""
    name: str
    weight: float
    dimension: str
    groups: List[str]


class CreateRecipeStepRequestModel(BaseModel):
    """Model for recipe step """
    step_num: int
    content: str


class CreateRecipeRequestModel(BaseModel):
    """Model for recipe creation"""
    title: str = Form()
    """recipe title"""
    time: int = Form()
    """cooking time"""
    complexity: str = Form()
    """complexity (medium / hard / etc...)"""
    servings: int = Form()
    """servings"""
    categories: List[str] = Form()
    """recipe categories (dinner, snack, etc..)"""
    steps: List[CreateRecipeStepRequestModel] = Form(...)
    """recipe steps (each step as an object. Check CreateRecipeStepRequestModel)"""
    ingredients: List[CreateRecipeIngredientRequestModel] = Form()
    """recipe ingredients (each ingredient as an object. Check CreateRecipeIngredientRequestModel)"""


class CreateCompilationRequestModel(BaseModel):
    """Model for recipe compilation creation"""
    recipe_ids: List[int]
    title: str
    image: UploadFile


class RecipeLikesRequestModel(BaseModel):
    """Model for recipe liking"""
    recipe_id: int


class RecipeCategoryResponseModel(BaseModel):
    """Model for recipe category with image"""
    name: str
    image: str


class RecipeCategoriesResponseModel(BaseModel):
    """Model for response recipe categories (with images, for showing categories list)"""
    categories: List[RecipeCategoryResponseModel]


class RecipeCompilationResponseModel(BaseModel):
    """Model for recipe compilation with image"""
    name: str
    image: str


class RecipeCompilationsResponseModel(BaseModel):
    """Model for response recipe compilation (with images, for showing categories list)"""
    compilations: List[RecipeCompilationResponseModel]


class RecipeFindResponseModel(BaseModel):
    """Model for search recipes by title"""
    title: str
    recipe_id: int


class IngredientFindResponseModel(BaseModel):
    """Model for search recipes by ingredient"""
    name: str
    ingredient_id: int


class CategoryFindResponseModel(BaseModel):
    """Model for search recipes by category"""
    name: str
    category_id: int


class FindResponseModel(BaseModel):
    """Model for search recipes by recipe titles, ingredient names and recipe categories"""
    recipes: List[RecipeFindResponseModel]
    """found recipes where title contains string"""
    ingredients: List[IngredientFindResponseModel]
    """found recipes where ingredient names contains string"""
    categories: List[CategoryFindResponseModel]
    """found recipes where category names contains string"""


class FindRequestModel(BaseModel):
    """Model for request to search recipe with string"""
    string_to_find: str


class RecipeIngredientResponseModel(BaseModel):
    """Model for recipe ingredient response"""
    name: str
    value: float
    dimension: str


class RecipeResponseModel(BaseModel):
    """Model for recipe response"""
    id: int
    """recipe id"""
    title: str
    """recipe title"""
    image: Optional[str]
    """recipe image link"""
    time: int
    """recipe cooking time"""
    complexity: str
    """recipe complexity (easy / medium / etc..)"""
    ingredients: List[RecipeIngredientResponseModel]
    """list of recipe ingredients"""
    steps: List[str]
    """list of recipe steps"""
    categories: List[str]
    """list of recipe categories"""
    servings: int
    """servings count"""
    liked: bool
    """is recipe liked by user who requested it"""


class GetRecipesRecipeResponseModel(BaseModel):
    """Model with not full recipe info for listed recipes response"""
    id: int
    """recipe id"""
    title: str
    """recipe title"""
    image: Optional[str]
    """link to recipe image"""
    time: int
    """recipe cooking time"""
    complexity: str
    """recipe complexity (easy / medium / etc...)"""
    servings: int
    """recipe servings"""
    liked: bool
    """is recipe liked by user who requested it"""


class GetRecipesResponseModel(BaseModel):
    """Model for listed recipes response"""
    recipes: List[GetRecipesRecipeResponseModel]


class GetIngredientsResponseModel(BaseModel):
    """Model for listed available ingredients response"""
    ingredients: List[str]


class GetDimensionsResponseModel(BaseModel):
    """Model for listed available ingredients response"""
    dimensions: List[str]


class GetIngredientGroupsResponseModel(BaseModel):
    """Model for listed available ingredients response"""
    ingredients: List[str]
