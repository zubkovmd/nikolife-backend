"""
Script that updates database to last revision.
Usage from root folder: ``python app/alembic_revision``.
"""

from alembic import command
from alembic.config import Config

alembic_cfg = Config("app/alembic.ini")
command.upgrade(alembic_cfg, "head")
