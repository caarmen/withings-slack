import asyncio
import dataclasses
import datetime
import logging
from typing import AsyncContextManager, Callable

from slackhealthbot.core.exceptions import UserLoggedOutException
from slackhealthbot.domain.localrepository.localfitbitrepository import (
    LocalFitbitRepository,
    UserIdentity,
)
from slackhealthbot.domain.remoterepository.remoteslackrepository import (
    RemoteSlackRepository,
)
from slackhealthbot.domain.usecases.fitbit import (
    usecase_process_new_activity,
    usecase_process_new_sleep,
)
from slackhealthbot.domain.usecases.slack import usecase_post_user_logged_out
from slackhealthbot.settings import settings


@dataclasses.dataclass
class Cache:
    cache_sleep_success: dict[str, datetime.date] = dataclasses.field(
        default_factory=dict
    )
    cache_fail: dict[str, datetime.date] = dataclasses.field(default_factory=dict)


async def handle_success_poll(
    fitbit_userid: str,
    when: datetime.date,
    cache: Cache,
):
    cache.cache_sleep_success[fitbit_userid] = when
    cache.cache_fail.pop(fitbit_userid, None)


async def handle_fail_poll(
    slack_repo: RemoteSlackRepository,
    fitbit_userid: str,
    slack_alias: str,
    when: datetime.date,
    cache: Cache,
):
    last_error_post = cache.cache_fail.get(fitbit_userid)
    if not last_error_post or last_error_post < when:
        await usecase_post_user_logged_out.do(
            repo=slack_repo,
            slack_alias=slack_alias,
            service="fitbit",
        )
        cache.cache_fail[fitbit_userid] = when


async def fitbit_poll(
    cache: Cache,
    fitbit_repo: LocalFitbitRepository,
    slack_repo: RemoteSlackRepository,
):
    logging.info("fitbit poll")
    today = datetime.date.today()
    try:
        await do_poll(
            fitbit_repo=fitbit_repo,
            slack_repo=slack_repo,
            cache=cache,
            when=today,
        )
    except Exception:
        logging.error("Error polling fitbit", exc_info=True)


async def do_poll(
    fitbit_repo: LocalFitbitRepository,
    slack_repo: RemoteSlackRepository,
    cache: Cache,
    when: datetime.date,
):
    user_identities: list[UserIdentity] = await fitbit_repo.get_all_user_identities()
    for user_identity in user_identities:
        await fitbit_poll_sleep(
            fitbit_repo=fitbit_repo,
            slack_repo=slack_repo,
            cache=cache,
            when=when,
            user_identity=user_identity,
        )
        await fitbit_poll_activity(
            fitbit_repo=fitbit_repo,
            slack_repo=slack_repo,
            cache=cache,
            when=when,
            user_identity=user_identity,
        )


async def fitbit_poll_activity(
    fitbit_repo: LocalFitbitRepository,
    slack_repo: RemoteSlackRepository,
    cache: Cache,
    when: datetime.date,
    user_identity: UserIdentity,
):
    try:
        await usecase_process_new_activity.do(
            fitbit_repo=fitbit_repo,
            slack_repo=slack_repo,
            fitbit_userid=user_identity.fitbit_userid,
            when=datetime.datetime.now(),
        )
    except UserLoggedOutException:
        await handle_fail_poll(
            slack_repo=slack_repo,
            fitbit_userid=user_identity.fitbit_userid,
            slack_alias=user_identity.slack_alias,
            when=when,
            cache=cache,
        )


async def fitbit_poll_sleep(
    fitbit_repo: LocalFitbitRepository,
    slack_repo: RemoteSlackRepository,
    cache: Cache,
    when: datetime.date,
    user_identity: UserIdentity,
):
    latest_successful_poll = cache.cache_sleep_success.get(user_identity.fitbit_userid)
    if not latest_successful_poll or latest_successful_poll < when:
        try:
            sleep_data = await usecase_process_new_sleep.do(
                fitbit_repo=fitbit_repo,
                slack_repo=slack_repo,
                fitbit_userid=user_identity.fitbit_userid,
                when=when,
            )
        except UserLoggedOutException:
            await handle_fail_poll(
                slack_repo=slack_repo,
                fitbit_userid=user_identity.fitbit_userid,
                slack_alias=user_identity.slack_alias,
                when=when,
                cache=cache,
            )
        else:
            if sleep_data:
                await handle_success_poll(
                    fitbit_userid=user_identity.fitbit_userid,
                    when=when,
                    cache=cache,
                )


async def schedule_fitbit_poll(
    fitbit_repo_factory: Callable[[], AsyncContextManager[LocalFitbitRepository]],
    slack_repo: RemoteSlackRepository,
    initial_delay_s: int = settings.fitbit_poll_interval_s,
    cache: Cache = None,
):
    if cache is None:
        cache = Cache()

    async def run_with_delay():
        await asyncio.sleep(initial_delay_s)
        while True:
            async with fitbit_repo_factory() as fitbit_repo:
                await fitbit_poll(
                    cache=cache,
                    fitbit_repo=fitbit_repo,
                    slack_repo=slack_repo,
                )
            await asyncio.sleep(settings.fitbit_poll_interval_s)

    return asyncio.create_task(run_with_delay())
