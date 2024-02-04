from slackhealthbot.domain.models.sleep import SleepData
from slackhealthbot.repositories import fitbitrepository


def core_sleep_to_repository_sleep(
    domain: SleepData | None,
) -> fitbitrepository.Sleep | None:
    if not domain:
        return None
    return fitbitrepository.Sleep(
        start_time=domain.start_time,
        end_time=domain.end_time,
        sleep_minutes=domain.sleep_minutes,
        wake_minutes=domain.wake_minutes,
    )
