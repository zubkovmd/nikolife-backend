import fastapi
from datetime import timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.routes.v1.utils.auth import authenticate_user, Token, create_access_token
from app.constants import ACCESS_TOKEN_EXPIRE_MINUTES
from app.api.routes.v1.users.router import router as users_router
from app.api.routes.v1.recipes.router import router as recipes_router
from app.api.routes.v1.blog.router import router as blog_router

router = fastapi.APIRouter(prefix="/v1")
router.include_router(users_router)
router.include_router(recipes_router)
router.include_router(blog_router)


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}














