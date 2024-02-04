from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import WeightData
from slackhealthbot.domain.usecases.slack import usecase_post_weight
from slackhealthbot.domain.usecases.withings import usecase_get_last_weight
from slackhealthbot.repositories import withingsrepository


async def do(
    db: AsyncSession,
    withings_userid: str,
    startdate: int,
    enddate: int,
):
    weight_data: WeightData = await usecase_get_last_weight.do(
        db=db,
        withings_userid=withings_userid,
        startdate=startdate,
        enddate=enddate,
    )
    await withingsrepository.update_user_weight(
        db=db,
        withings_userid=withings_userid,
        last_weight_kg=weight_data.weight_kg,
    )
    await usecase_post_weight.do(weight_data)
