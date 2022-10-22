from typing import List

from fastapi import UploadFile
from fastapi.params import Form
from pydantic import BaseModel


class GetStoriesResponseModel(BaseModel):

    class GetStoryResponseModel(BaseModel):
        title: str
        thumbnail: str
        images: List[str]

    stories: List[GetStoryResponseModel]


class PutStoriesResponseModel(BaseModel):
    images: List[UploadFile] = Form(default=None)
    title: str = Form(default=None)


class GetArticlesResponseModel(BaseModel):

    class GetArticleResponseModel(BaseModel):
        title: str
        subtitle: str
        created_at: str
        text: str
        image: str
        user_id: int

    articles: List[GetArticleResponseModel]
