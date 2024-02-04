from slackhealthbot.core.models import SleepData
from slackhealthbot.repositories import fitbitrepository


def repository_sleep_to_core_sleep(
    repo: fitbitrepository.Sleep | None,
) -> SleepData | None:
    if not repo:
        return None
    return SleepData(
        start_time=repo.start_time,
        end_time=repo.end_time,
        sleep_minutes=repo.sleep_minutes,
        wake_minutes=repo.wake_minutes,
    )
