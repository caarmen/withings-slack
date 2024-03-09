from slackhealthbot.domain.models.activity import (
    ActivityData,
    ActivityZone,
    ActivityZoneMinutes,
)
from slackhealthbot.remoteservices.fitbit.activityapi import FitbitActivities


def remote_service_activity_to_domain_activity(
    remote: FitbitActivities | None,
) -> tuple[str, ActivityData] | None:
    if not remote or not remote.activities:
        return None
    fitbit_activity = remote.activities[0]
    return fitbit_activity.activityName, ActivityData(
        log_id=fitbit_activity.logId,
        type_id=fitbit_activity.activityTypeId,
        calories=fitbit_activity.calories,
        total_minutes=fitbit_activity.duration // 60000,
        zone_minutes=[
            ActivityZoneMinutes(zone=ActivityZone[x.type.upper()], minutes=x.minutes)
            for x in fitbit_activity.activeZoneMinutes.minutesInHeartRateZones
            if x.minutes > 0
        ],
    )
