"""
In this module FastAPI application is initializing.
"""

import sentry_sdk
import fastapi

from fastapi.middleware.cors import CORSMiddleware

from prometheus_fastapi_instrumentator import Instrumentator
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.api.admin import create_admin
from app.api.routes.root import router
from app.config import settings
from app.utils.utility import create_superuser

if settings.sentry:
    sentry_sdk.init(
        dsn=settings.sentry.dsn,
        environment=settings.environment,
        integrations=[SqlalchemyIntegration()],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production,
        traces_sample_rate=1.0,
    )

app = fastapi.FastAPI()
@app.on_event("startup")
async def startup():
    """startup methods for FastAPI application"""
    Instrumentator().instrument(app).expose(app)
    if settings.environment == "development":
        await create_superuser()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
create_admin(app)

