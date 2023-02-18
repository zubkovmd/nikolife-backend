"""Module contains blog models that service uses"""

from typing import List

from fastapi import UploadFile
from fastapi.params import Form
from pydantic import BaseModel


class GetStoriesResponseModel(BaseModel):
    """response model for stories request"""
    class GetStoryResponseModel(BaseModel):
        """response model for one story"""
        id: int
        title: str
        thumbnail: str
        images: List[str]

    stories: List[GetStoryResponseModel]


class PutStoriesResponseModel(BaseModel):
    """response model for story adding request"""
    images: List[UploadFile] = Form(default=None)
    title: str = Form(default=None)


class GetArticlesResponseModel(BaseModel):
    """response model for articles request"""
    class GetArticleResponseModel(BaseModel):
        """response model for one article"""
        id: int
        title: str
        subtitle: str
        created_at: str
        text: str
        image: str
        user_id: int

    articles: List[GetArticleResponseModel]
