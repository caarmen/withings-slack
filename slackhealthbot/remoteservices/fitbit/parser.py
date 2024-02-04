import datetime
import json
import logging
from typing import Annotated, Literal, Optional, Self, Union

from pydantic import BaseModel, Field

from slackhealthbot.core.models import ActivityData, ActivityZoneMinutes, SleepData


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
        logging.info(f"parse sleep input: {input}")
        return cls(**json.loads(input))


class FitbitMinutesInHeartRateZone(BaseModel):
    minutes: int
    type: str


class FitBitActiveZoneMinutes(BaseModel):
    minutesInHeartRateZones: list[FitbitMinutesInHeartRateZone]


class FitbitActivity(BaseModel):
    logId: int
    activeZoneMinutes: FitBitActiveZoneMinutes = FitBitActiveZoneMinutes(
        minutesInHeartRateZones=[]
    )
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


def parse_sleep(input: str) -> Optional[SleepData]:
    try:
        fitbit_sleep = FitbitSleep.parse(input)
    except Exception as e:
        logging.warning(f"Error parsing sleep: error {e}, input: {input}", exc_info=e)
        return None
    main_sleep_item = next(
        (item for item in fitbit_sleep.sleep if item.isMainSleep), None
    )
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


def parse_activity(input: str) -> Optional[ActivityData]:
    try:
        fitbit_activities = FitbitActivities.parse(input)
    except Exception as e:
        logging.warning(
            f"Error parsing activity: error {e}, input: {input}", exc_info=e
        )
        return None
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
