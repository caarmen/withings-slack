from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.localrepository.localwithingsrepository import (
    LocalWithingsRepository,
)
from slackhealthbot.remoteservices.api.withings import weightapi


async def do(
    repo: LocalWithingsRepository,
    withings_userid: str,
    startdate: int,
    enddate: int,
) -> float:
    oauth_data: OAuthFields = await repo.get_oauth_data_by_withings_userid(
        withings_userid=withings_userid,
    )
    return await weightapi.get_last_weight_kg(
        oauth_token=oauth_data,
        startdate=startdate,
        enddate=enddate,
    )
