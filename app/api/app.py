import sentry_sdk
import fastapi

from prometheus_fastapi_instrumentator import Instrumentator
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from app.api.routes.root import router
from app.config import Settings

sentry_sdk.init(
    dsn=Settings().sentry.dsn,
    environment=Settings().environment,
    integrations=[SqlalchemyIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production,
    traces_sample_rate=1.0,
)

app = fastapi.FastAPI()
app.include_router(router)

@app.on_event("startup")
async def startup():
    Instrumentator().instrument(app).expose(app)
