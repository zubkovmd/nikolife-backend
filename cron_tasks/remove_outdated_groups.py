import asyncio
import datetime

import sqlalchemy

from app.database import DatabaseManagerAsync
from app.database.models.base import association_users_groups


async def remove_outdated_groups():
    async with DatabaseManagerAsync.get_instance().get_session() as session:
        stmt = (
            sqlalchemy.delete(association_users_groups)
            .where(association_users_groups.c.expiration_time < datetime.datetime.now())
        )
        await session.execute(stmt)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(remove_outdated_groups())

