import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import SleepData
from slackhealthbot.remoteservices.fitbit import sleepapi
from slackhealthbot.repositories import fitbitrepository


async def do(
    db: AsyncSession,
    fitbit_userid: str,
    when: datetime.date,
) -> SleepData | None:
    user: fitbitrepository.User = await fitbitrepository.get_user_by_fitbit_userid(
        db,
        fitbit_userid=fitbit_userid,
    )
    last_sleep: sleepapi.FitbitSleep = await sleepapi.get_sleep(
        oauth_token=user.oauth_data,
        when=when,
    )
    return parse_sleep(last_sleep) if last_sleep else None


def parse_sleep(fitbit_sleep: sleepapi.FitbitSleep) -> SleepData | None:
    main_sleep_item = next(
        (item for item in fitbit_sleep.sleep if item.isMainSleep), None
    )
    if not main_sleep_item:
        logging.warning("No main sleep found")
        return None

    wake_minutes = (
        main_sleep_item.levels.summary.awake.minutes
        if main_sleep_item.type == "classic"
        else main_sleep_item.levels.summary.wake.minutes
    )
    asleep_minutes = (
        main_sleep_item.levels.summary.asleep.minutes
        if main_sleep_item.type == "classic"
        else main_sleep_item.duration / 60000 - wake_minutes
    )
    return SleepData(
        start_time=datetime.datetime.strptime(
            main_sleep_item.startTime, DATETIME_FORMAT
        ),
        end_time=datetime.datetime.strptime(main_sleep_item.endTime, DATETIME_FORMAT),
        sleep_minutes=asleep_minutes,
        wake_minutes=wake_minutes,
    )


DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
