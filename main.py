"""
Root module. Application should start with ``app`` object.
You can start application with ``$ uvicorn main:app`` from root folder
or use main script with ``python main.py``.
"""

import uvicorn

from app.api.app import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)