"""Utility methods for user routes"""

from typing import Optional

import requests
import sqlalchemy
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from app.database.models.base import Users


