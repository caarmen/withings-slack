from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.domain.models.weight import WeightData
from slackhealthbot.remoteservices.withings import weightapi
from slackhealthbot.repositories import withingsrepository


async def do(
    db: AsyncSession,
    withings_userid: str,
    startdate: int,
    enddate: int,
) -> WeightData:
    user: withingsrepository.User = (
        await withingsrepository.get_user_by_withings_userid(
            db,
            withings_userid=withings_userid,
        )
    )
    last_weight_kg = await weightapi.get_last_weight_kg(
        oauth_token=user.oauth_data,
        startdate=startdate,
        enddate=enddate,
    )
    return WeightData(
        weight_kg=last_weight_kg,
        slack_alias=user.identity.slack_alias,
        last_weight_kg=user.fitness_data.last_weight_kg,
    )
