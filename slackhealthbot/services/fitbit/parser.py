import datetime
import json
from typing import Annotated, Literal, Optional, Self, Union

from pydantic import BaseModel, Field

from slackhealthbot.services import models as svc_models


class FitbitSleepItemSummaryItem(BaseModel):
    minutes: int


class FitbitClassicSleepItemSummary(BaseModel):
    awake: FitbitSleepItemSummaryItem
    asleep: FitbitSleepItemSummaryItem


class FitbitStagesSleepItemSummary(BaseModel):
    wake: FitbitSleepItemSummaryItem


class FitbitStagesSleepItemLevels(BaseModel):
    summary: FitbitStagesSleepItemSummary


class FitbitClassicSleepItemLevels(BaseModel):
    summary: FitbitClassicSleepItemSummary


class FitbitSleepItem(BaseModel):
    duration: int
    endTime: str
    isMainSleep: bool
    startTime: str


class FitbitClassicSleepItem(FitbitSleepItem):
    type: Literal["classic"]
    levels: FitbitClassicSleepItemLevels


class FitbitStagesSleepItem(FitbitSleepItem):
    type: Literal["stages"]
    levels: FitbitStagesSleepItemLevels


class FitbitSleep(BaseModel):
    sleep: list[
        Annotated[
            Union[FitbitClassicSleepItem, FitbitStagesSleepItem],
            Field(discriminator="type"),
        ]
    ]

    @classmethod
    def parse(cls, input: str) -> Self:
        return cls(**json.loads(input))


class FitbitMinutesInHeartRateZone(BaseModel):
    minutes: int
    zoneName: str


class FitBitActiveZoneMinutes(BaseModel):
    minutesInHeartRateZones: list[FitbitMinutesInHeartRateZone]


class FitbitActivity(BaseModel):
    logId: int
    activeZoneMinutes: FitBitActiveZoneMinutes
    activityName: str
    activityTypeId: int
    calories: int
    duration: int


class FitbitActivities(BaseModel):
    activities: list[FitbitActivity]

    @classmethod
    def parse(cls, input: str) -> Self:
        return cls(**json.loads(input))


DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


def parse_sleep(input: str, slack_alias: str) -> Optional[svc_models.SleepData]:
    fitbit_sleep = FitbitSleep.parse(input)
    main_sleep_item = next(
        (item for item in fitbit_sleep.sleep if item.isMainSleep), None
    )
    if not main_sleep_item:
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
    return svc_models.SleepData(
        start_time=datetime.datetime.strptime(
            main_sleep_item.startTime, DATETIME_FORMAT
        ),
        end_time=datetime.datetime.strptime(main_sleep_item.endTime, DATETIME_FORMAT),
        sleep_minutes=asleep_minutes,
        wake_minutes=wake_minutes,
        slack_alias=slack_alias,
    )


def parse_activity(input: str) -> Optional[svc_models.ActivityData]:
    fitbit_activities = FitbitActivities.parse(input)
    if not fitbit_activities.activities:
        return None
    fitbit_activity = fitbit_activities.activities[0]
    return svc_models.ActivityData(
        log_id=fitbit_activity.logId,
        type_id=fitbit_activity.activityTypeId,
        name=fitbit_activity.activityName,
        calories=fitbit_activity.calories,
        total_minutes=fitbit_activity.duration / 60000,
        zone_minutes=[
            svc_models.ActivityZoneMinutes(name=x.zoneName, minutes=x.minutes)
            for x in fitbit_activity.activeZoneMinutes.minutesInHeartRateZones
            if x.minutes > 0
        ],
    )
