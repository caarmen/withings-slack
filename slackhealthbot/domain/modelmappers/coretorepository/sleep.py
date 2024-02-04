from slackhealthbot.core.models import SleepData
from slackhealthbot.repositories import fitbitrepository


def core_sleep_to_repository_sleep(
    core: SleepData | None,
) -> fitbitrepository.Sleep | None:
    if not core:
        return None
    return fitbitrepository.Sleep(
        start_time=core.start_time,
        end_time=core.end_time,
        sleep_minutes=core.sleep_minutes,
        wake_minutes=core.wake_minutes,
    )
