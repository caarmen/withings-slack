import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import ActivityData
from slackhealthbot.domain.modelmappers.remoteservicetocore.activity import (
    remote_service_activity_to_core_activity,
)
from slackhealthbot.remoteservices.fitbit import activityapi
from slackhealthbot.repositories import fitbitrepository


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
    return remote_service_activity_to_core_activity(last_activities)
