import asyncio
import dataclasses
import datetime
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.database import models
from slackhealthbot.database.connection import SessionLocal
from slackhealthbot.services import slack
from slackhealthbot.services.exceptions import UserLoggedOutException
from slackhealthbot.services.fitbit import api as fitbit_api
from slackhealthbot.services.fitbit import service
from slackhealthbot.services.models import SleepData, user_last_sleep_data
from slackhealthbot.settings import settings


@dataclasses.dataclass
class Cache:
    cache_sleep_success: dict[str, datetime.date] = dataclasses.field(
        default_factory=dict
    )
    cache_fail: dict[str, datetime.date] = dataclasses.field(default_factory=dict)


async def handle_success_poll(
    db: AsyncSession,
    fitbit_user: models.FitbitUser,
    sleep_data: Optional[SleepData],
    when: datetime.date,
    cache: Cache,
):
    if sleep_data:
        last_sleep_data = user_last_sleep_data(fitbit_user)
        await service.save_new_sleep_data(db, fitbit_user.user, sleep_data)
        await slack.post_sleep(
            slack_alias=fitbit_user.user.slack_alias,
            new_sleep_data=sleep_data,
            last_sleep_data=last_sleep_data,
        )
        cache.cache_sleep_success[fitbit_user.oauth_userid] = when
        cache.cache_fail.pop(fitbit_user.oauth_userid, None)


async def handle_fail_poll(
    fitbit_user: models.FitbitUser,
    when: datetime.date,
    cache: Cache,
):
    last_error_post = cache.cache_fail.get(fitbit_user.oauth_userid)
    if not last_error_post or last_error_post < when:
        await slack.post_user_logged_out(
            slack_alias=fitbit_user.user.slack_alias,
            service="fitbit",
        )
        cache.cache_fail[fitbit_user.oauth_userid] = when


async def fitbit_poll(cache: Cache):
    logging.info("fitbit poll")
    today = datetime.date.today()
    try:
        async with SessionLocal() as db:
            await do_poll(db, cache, when=today)
    except Exception:
        logging.error("Error polling fitbit", exc_info=True)
    await schedule_fitbit_poll(cache=cache)


async def do_poll(db: AsyncSession, cache: Cache, when: datetime.date):
    fitbit_users = await db.scalars(
        statement=select(models.FitbitUser).join(models.FitbitUser.user),
    )
    for fitbit_user in fitbit_users:
        await fitbit_poll_sleep(db, cache, when, fitbit_user)
        await fitbit_poll_activity(db, cache, when, fitbit_user)


async def fitbit_poll_activity(
    db: AsyncSession,
    cache: Cache,
    when: datetime.date,
    fitbit_user: models.FitbitUser,
):
    try:
        activity_data = await service.get_activity(
            db,
            user=fitbit_user.user,
            when=datetime.datetime.now(),
        )
        if activity_data:
            await slack.post_activity(
                slack_alias=fitbit_user.user.slack_alias,
                activity_data=activity_data,
            )

    except UserLoggedOutException:
        await handle_fail_poll(
            fitbit_user=fitbit_user,
            when=when,
            cache=cache,
        )


async def fitbit_poll_sleep(
    db: AsyncSession,
    cache: Cache,
    when: datetime.date,
    fitbit_user: models.FitbitUser,
):
    latest_successful_poll = cache.cache_sleep_success.get(fitbit_user.oauth_userid)
    if not latest_successful_poll or latest_successful_poll < when:
        try:
            sleep_data = await fitbit_api.get_sleep(
                db,
                user=fitbit_user.user,
                when=when,
            )
        except UserLoggedOutException:
            await handle_fail_poll(
                fitbit_user=fitbit_user,
                when=when,
                cache=cache,
            )
        else:
            await handle_success_poll(
                db=db,
                fitbit_user=fitbit_user,
                sleep_data=sleep_data,
                when=when,
                cache=cache,
            )


async def schedule_fitbit_poll(
    delay_s: int = settings.fitbit_poll_interval_s, cache: Cache = None
):
    if cache is None:
        cache = Cache()
    loop = asyncio.get_event_loop()
    loop.call_later(float(delay_s), asyncio.create_task, fitbit_poll(cache))
