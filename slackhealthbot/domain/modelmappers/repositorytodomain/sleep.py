from slackhealthbot.data.repositories import fitbitrepository
from slackhealthbot.domain.models.sleep import SleepData


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
