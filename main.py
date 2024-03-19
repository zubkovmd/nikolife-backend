"""
Root module. Application should start with ``app`` object.
You can start application with ``$ uvicorn main:app`` from root folder
or use main script with ``python main.py``.
"""

import uvicorn

from uvicorn.config import LOGGING_CONFIG

from app.api.app import app

LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)