from typing import List

import sqlalchemy

from app.api.routes.v1.groups.utils import get_group_model_or_create_if_not_exists
from app.constants import ADMIN_GROUP_NAME, DEV_SUPERUSER_LOGIN, DEV_SUPERUSER_PASSWORD
from app.database.manager import DatabaseManagerAsync

from app.log import Loggers


def filter_dict_with_key_list(dictionary: dict, key_list: List[str]):
    return {key: dictionary[key] for key in key_list}


async def create_superuser() -> None:
    """
    Method creates superuser (admin) for development.

    :return: None
    """
    from app.database.models.base import Users
    logger = Loggers.get_default_logger()
    logger.info("Creating superuser")
    async with DatabaseManagerAsync.get_instance().get_session() as session:
        user_is_already_created = (
            await session.execute(sqlalchemy.select(Users).where(Users.username == DEV_SUPERUSER_LOGIN))
        ).scalars().first()
        if user_is_already_created:
            logger.info("Superuser already created")
            return
        new_user = Users(
            username=DEV_SUPERUSER_LOGIN,
            password=DEV_SUPERUSER_PASSWORD,
            email=DEV_SUPERUSER_LOGIN,
            name=DEV_SUPERUSER_LOGIN,
            info=DEV_SUPERUSER_LOGIN,
        )
        new_user.groups.append(await get_group_model_or_create_if_not_exists(group_name=ADMIN_GROUP_NAME,
                                                                             session=session))
        session.add(new_user)
        logger.info("Superuser created")
