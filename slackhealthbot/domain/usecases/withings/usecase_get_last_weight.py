from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.data.repositories import withingsrepository
from slackhealthbot.remoteservices.withings import weightapi


async def do(
    db: AsyncSession,
    withings_userid: str,
    startdate: int,
    enddate: int,
) -> float:
    oauth_data: withingsrepository.OAuthData = (
        await withingsrepository.get_oauth_data_by_withings_userid(
            db,
            withings_userid=withings_userid,
        )
    )
    return await weightapi.get_last_weight_kg(
        oauth_token=oauth_data,
        startdate=startdate,
        enddate=enddate,
    )
