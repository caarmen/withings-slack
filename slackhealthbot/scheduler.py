import asyncio
import dataclasses
import datetime
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import SleepData
from slackhealthbot.database import models
from slackhealthbot.database.connection import SessionLocal
from slackhealthbot.domain.fitbit import (
    usecase_process_new_activity,
    usecase_process_new_sleep,
)
from slackhealthbot.services import slack
from slackhealthbot.services.exceptions import UserLoggedOutException
from slackhealthbot.settings import settings


@dataclasses.dataclass
class Cache:
    cache_sleep_success: dict[str, datetime.date] = dataclasses.field(
        default_factory=dict
    )
    cache_fail: dict[str, datetime.date] = dataclasses.field(default_factory=dict)


async def handle_success_poll(
    fitbit_userid: str,
    sleep_data: Optional[SleepData],
    when: datetime.date,
    cache: Cache,
):
    if sleep_data:
        cache.cache_sleep_success[fitbit_userid] = when
        cache.cache_fail.pop(fitbit_userid, None)


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
        await usecase_process_new_activity.do(
            db=db,
            fitbit_userid=fitbit_user.oauth_userid,
            when=datetime.datetime.now(),
        )
        await db.refresh(fitbit_user)
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
            sleep_data: SleepData = await usecase_process_new_sleep.do(
                db,
                fitbit_userid=fitbit_user.oauth_userid,
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
                fitbit_userid=fitbit_user.oauth_userid,
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
