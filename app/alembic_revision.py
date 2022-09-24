from datetime import datetime

from alembic import command
from alembic.config import Config

message = input("Введите краткое описание миграции (eng): ")
alembic_cfg = Config("app/alembic.ini")

date = datetime.now().strftime("%Y_%m_%d_%H%M")
command.revision(alembic_cfg, message=message, autogenerate=True, rev_id=f"{date}")
