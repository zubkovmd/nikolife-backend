import fastapi
from app.api.routes.v1.router import router as router_v1

router = fastapi.APIRouter(
    prefix="/api"
)

router.include_router(router_v1)