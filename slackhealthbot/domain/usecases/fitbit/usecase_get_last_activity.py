import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.data.repositories import fitbitrepository
from slackhealthbot.domain.modelmappers.remoteservicetodomain.activity import (
    remote_service_activity_to_domain_activity,
)
from slackhealthbot.domain.models.activity import ActivityData
from slackhealthbot.remoteservices.fitbit import activityapi


async def do(
    db: AsyncSession,
    fitbit_userid: str,
    when: datetime.date,
) -> ActivityData | None:
    user: fitbitrepository.User = await fitbitrepository.get_user_by_fitbit_userid(
        db,
        fitbit_userid=fitbit_userid,
    )
    last_activities: activityapi.FitbitActivities = await activityapi.get_activity(
        oauth_token=user.oauth_data,
        when=when,
    )
    return remote_service_activity_to_domain_activity(last_activities)
