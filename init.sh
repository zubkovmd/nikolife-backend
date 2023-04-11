#!/bin/bash
echo "$(locale -a)"
echo "0 * * * * python3 /proj/app/remove_outdated_groups.py" >> cron_tasks
crontab cron_tasks
rm cron_tasks
python app/alembic_upgrade_head.py
uvicorn main:app --host 0.0.0.0 --port 80