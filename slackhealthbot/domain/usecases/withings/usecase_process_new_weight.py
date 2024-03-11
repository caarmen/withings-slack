from slackhealthbot.domain.localrepository.localwithingsrepository import (
    LocalWithingsRepository,
    User,
)
from slackhealthbot.domain.models.weight import WeightData
from slackhealthbot.domain.usecases.slack import usecase_post_weight
from slackhealthbot.domain.usecases.withings import usecase_get_last_weight


async def do(
    repo: LocalWithingsRepository,
    withings_userid: str,
    startdate: int,
    enddate: int,
):
    user: User = await repo.get_user_by_withings_userid(
        withings_userid=withings_userid,
    )
    previous_weight_kg: float = user.fitness_data.last_weight_kg

    new_weight_kg: float = await usecase_get_last_weight.do(
        repo=repo,
        withings_userid=withings_userid,
        startdate=startdate,
        enddate=enddate,
    )
    await repo.update_user_weight(
        withings_userid=withings_userid,
        last_weight_kg=new_weight_kg,
    )
    await usecase_post_weight.do(
        WeightData(
            weight_kg=new_weight_kg,
            slack_alias=user.identity.slack_alias,
            last_weight_kg=previous_weight_kg,
        )
    )
