import datetime

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.localrepository.localfitbitrepository import (
    LocalFitbitRepository,
)
from slackhealthbot.domain.models.sleep import SleepData
from slackhealthbot.domain.remoterepository.remotefitbitrepository import (
    RemoteFitbitRepository,
)


async def do(
    local_repo: LocalFitbitRepository,
    remote_repo: RemoteFitbitRepository,
    fitbit_userid: str,
    when: datetime.date,
) -> SleepData | None:
    oauth_data: OAuthFields = await local_repo.get_oauth_data_by_fitbit_userid(
        fitbit_userid=fitbit_userid,
    )
    return await remote_repo.get_sleep(
        oauth_fields=oauth_data,
        when=when,
    )
