from typing import Optional

from pydantic import BaseModel


#  DEFAULT RESPONSES
class DefaultResponse(BaseModel):
    detail: str


class ErrorResponse(DefaultResponse):
    pass

class DefaultResponseWithPayload(DefaultResponse):
    payload: dict



# USER RESPONSES
class User(BaseModel):
    username: str
    image: Optional[str]
    email: str
    name: str
    info: str


class UserRequestResponse(DefaultResponse):
    user: User


# RECIPE RESPONSES
class RecipeCreatedResponse(DefaultResponse):
    detail = "Рецепт был добавлен"
    new_recipe_id: int
