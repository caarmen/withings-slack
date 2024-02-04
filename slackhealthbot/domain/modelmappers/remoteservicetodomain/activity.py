from slackhealthbot.domain.models.activity import ActivityData, ActivityZoneMinutes
from slackhealthbot.remoteservices.fitbit.activityapi import FitbitActivities


def remote_service_activity_to_core_activity(
    remote: FitbitActivities | None,
) -> ActivityData | None:
    if not remote or not remote.activities:
        return None
    fitbit_activity = remote.activities[0]
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
