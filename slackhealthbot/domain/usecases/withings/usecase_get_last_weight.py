from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.localrepository.localwithingsrepository import (
    LocalWithingsRepository,
)
from slackhealthbot.domain.remoterepository.remotewithingsrepository import (
    RemoteWithingsRepository,
)


async def do(
    local_repo: LocalWithingsRepository,
    remote_repo: RemoteWithingsRepository,
    withings_userid: str,
    startdate: int,
    enddate: int,
) -> float:
    oauth_fields: OAuthFields = await local_repo.get_oauth_data_by_withings_userid(
        withings_userid=withings_userid,
    )
    return await remote_repo.get_last_weight_kg(
        oauth_fields=oauth_fields,
        startdate=startdate,
        enddate=enddate,
    )
