#!/bin/bash
echo "$(locale -a)"
python app/alembic_upgrade_head.py
uvicorn main:app --host 0.0.0.0 --port 80