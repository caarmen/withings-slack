import datetime

from slackhealthbot.domain.localrepository.localfitbitrepository import (
    LocalFitbitRepository,
    User,
)
from slackhealthbot.domain.modelmappers.remoteservicetodomain.activity import (
    remote_service_activity_to_domain_activity,
)
from slackhealthbot.domain.models.activity import ActivityData
from slackhealthbot.remoteservices.fitbit import activityapi


async def do(
    repo: LocalFitbitRepository,
    fitbit_userid: str,
    when: datetime.datetime,
) -> tuple[str, ActivityData] | None:
    user: User = await repo.get_user_by_fitbit_userid(
        fitbit_userid=fitbit_userid,
    )
    last_activities: activityapi.FitbitActivities = await activityapi.get_activity(
        oauth_token=user.oauth_data,
        when=when,
    )
    return remote_service_activity_to_domain_activity(last_activities)
