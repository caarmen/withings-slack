import asyncio
import datetime as dt
import logging
from typing import AsyncContextManager, Callable, Coroutine

from slackhealthbot.domain.localrepository.localfitbitrepository import (
    LocalFitbitRepository,
)
from slackhealthbot.domain.remoterepository.remoteslackrepository import (
    RemoteSlackRepository,
)
from slackhealthbot.domain.usecases.fitbit import usecase_process_daily_activities

logger = logging.getLogger(__name__)


async def post_daily_activities(
    local_fitbit_repo_factory: Callable[[], AsyncContextManager[LocalFitbitRepository]],
    activity_type_ids: set[int],
    slack_repo: RemoteSlackRepository,
    post_time: dt.time,
) -> Coroutine[None, None, asyncio.Task]:

    async def task():
        while True:
            now = dt.datetime.now()

            next_task_datetime = now.replace(
                hour=post_time.hour,
                minute=post_time.minute,
                second=post_time.second,
                microsecond=post_time.microsecond,
            )
            if next_task_datetime < now:
                next_task_datetime += dt.timedelta(days=1)
            time_until_next_task_datetime_s = (next_task_datetime - now).seconds
            logger.info(
                f"Sleeping {time_until_next_task_datetime_s} seconds until next daily summary at {next_task_datetime}"
            )
            await asyncio.sleep(time_until_next_task_datetime_s)

            async with local_fitbit_repo_factory() as local_fitbit_repo:
                await usecase_process_daily_activities.do(
                    local_fitbit_repo=local_fitbit_repo,
                    type_ids=activity_type_ids,
                    slack_repo=slack_repo,
                )

    return asyncio.create_task(task())
