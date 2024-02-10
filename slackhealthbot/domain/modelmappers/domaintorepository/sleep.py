from slackhealthbot.data.repositories import fitbitrepository
from slackhealthbot.domain.models.sleep import SleepData


def domain_sleep_to_repository_sleep(domain: SleepData) -> fitbitrepository.Sleep:
    return fitbitrepository.Sleep(
        start_time=domain.start_time,
        end_time=domain.end_time,
        sleep_minutes=domain.sleep_minutes,
        wake_minutes=domain.wake_minutes,
    )
