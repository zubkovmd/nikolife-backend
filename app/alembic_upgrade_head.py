from alembic import command
from alembic.config import Config

alembic_cfg = Config("app/alembic.ini")
command.upgrade(alembic_cfg, "head")
