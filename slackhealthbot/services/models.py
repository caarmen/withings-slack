from typing import Optional

from slackhealthbot.core.models import SleepData
from slackhealthbot.database.models import FitbitUser


def user_last_sleep_data(user: FitbitUser) -> Optional[SleepData]:
    return (
        SleepData(
            start_time=user.last_sleep_start_time,
            end_time=user.last_sleep_end_time,
            sleep_minutes=user.last_sleep_sleep_minutes,
            wake_minutes=user.last_sleep_wake_minutes,
        )
        if user.last_sleep_start_time
        else None
    )
