import datetime
import logging

from slackhealthbot.domain.models.sleep import SleepData
from slackhealthbot.remoteservices.api.fitbit import sleepapi


def remote_service_sleep_to_domain_sleep(
    remote: sleepapi.FitbitSleep | None,
) -> SleepData | None:
    if not remote:
        return None
    main_sleep_item = next((item for item in remote.sleep if item.isMainSleep), None)
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
