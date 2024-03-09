from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.repository.withingsrepository import WithingsRepository
from slackhealthbot.remoteservices.withings import weightapi


async def do(
    repo: WithingsRepository,
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
