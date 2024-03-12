import datetime

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.localrepository.localfitbitrepository import (
    LocalFitbitRepository,
)
from slackhealthbot.domain.modelmappers.remoteservicetodomain.sleep import (
    remote_service_sleep_to_domain_sleep,
)
from slackhealthbot.domain.models.sleep import SleepData
from slackhealthbot.remoteservices.api.fitbit import sleepapi


async def do(
    repo: LocalFitbitRepository,
    fitbit_userid: str,
    when: datetime.date,
) -> SleepData | None:
    oauth_data: OAuthFields = await repo.get_oauth_data_by_fitbit_userid(
        fitbit_userid=fitbit_userid,
    )
    last_sleep: sleepapi.FitbitSleep = await sleepapi.get_sleep(
        oauth_token=oauth_data,
        when=when,
    )
    return remote_service_sleep_to_domain_sleep(last_sleep)
