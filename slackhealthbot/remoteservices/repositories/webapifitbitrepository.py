import datetime
import logging

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.models.activity import (
    ActivityData,
    ActivityZone,
    ActivityZoneMinutes,
)
from slackhealthbot.domain.models.sleep import SleepData
from slackhealthbot.domain.remoterepository.remotefitbitrepository import (
    RemoteFitbitRepository,
)
from slackhealthbot.remoteservices.api.fitbit import activityapi, sleepapi, subscribeapi
from slackhealthbot.remoteservices.api.fitbit.activityapi import FitbitActivities
from slackhealthbot.remoteservices.api.fitbit.sleepapi import FitbitSleep


class WebApiFitbitRepository(RemoteFitbitRepository):
    async def subscribe(
        self,
        oauth_fields: OAuthFields,
    ):
        await subscribeapi.subscribe(oauth_fields)

    async def get_sleep(
        self,
        oauth_fields: OAuthFields,
        when: datetime.date,
    ) -> SleepData | None:
        sleep: FitbitSleep = await sleepapi.get_sleep(
            oauth_token=oauth_fields, when=when
        )
        return remote_service_sleep_to_domain_sleep(sleep) if sleep else None

    async def get_activity(
        self, oauth_fields: OAuthFields, when: datetime.datetime
    ) -> tuple[str, ActivityData] | None:
        activities: FitbitActivities | None = await activityapi.get_activity(
            oauth_token=oauth_fields,
            when=when,
        )
        return remote_service_activity_to_domain_activity(activities)


def remote_service_sleep_to_domain_sleep(
    remote: sleepapi.FitbitSleep | None,
) -> SleepData | None:
    if not remote:
        return None
    main_sleep_item = next((item for item in remote.sleep if item.isMainSleep), None)
    if not main_sleep_item:
        logging.warning("No main sleep found")
        return None

    wake_minutes = (
        main_sleep_item.levels.summary.awake.minutes
        if main_sleep_item.type == "classic"
        else main_sleep_item.levels.summary.wake.minutes
    )
    asleep_minutes = (
        main_sleep_item.levels.summary.asleep.minutes
        if main_sleep_item.type == "classic"
        else main_sleep_item.duration / 60000 - wake_minutes
    )
    return SleepData(
        start_time=datetime.datetime.strptime(
            main_sleep_item.startTime, DATETIME_FORMAT
        ),
        end_time=datetime.datetime.strptime(main_sleep_item.endTime, DATETIME_FORMAT),
        sleep_minutes=asleep_minutes,
        wake_minutes=wake_minutes,
    )


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


DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
