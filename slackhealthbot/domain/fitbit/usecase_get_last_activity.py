import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import ActivityData, ActivityZoneMinutes
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
    return parse_activity(last_activities) if last_activities else None


def parse_activity(
    fitbit_activities: activityapi.FitbitActivities,
) -> ActivityData | None:
    if not fitbit_activities.activities:
        return None
    fitbit_activity = fitbit_activities.activities[0]
    return ActivityData(
        log_id=fitbit_activity.logId,
        type_id=fitbit_activity.activityTypeId,
        name=fitbit_activity.activityName,
        calories=fitbit_activity.calories,
        total_minutes=fitbit_activity.duration // 60000,
        zone_minutes=[
            ActivityZoneMinutes(zone=x.type.lower(), minutes=x.minutes)
            for x in fitbit_activity.activeZoneMinutes.minutesInHeartRateZones
            if x.minutes > 0
        ],
    )
