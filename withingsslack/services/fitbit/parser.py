import json
from typing import Optional, Self
from withingsslack.services import models as svc_models
from pydantic import BaseModel
import datetime


class FitbitSleepItemSummaryItem(BaseModel):
    minutes: int


class FitbitSleepItemSummary(BaseModel):
    wake: FitbitSleepItemSummaryItem


class FitbitSleepItemLevels(BaseModel):
    summary: FitbitSleepItemSummary


class FitbitSleepItem(BaseModel):
    duration: int
    efficiency: int
    endTime: str
    isMainSleep: bool
    startTime: str
    levels: FitbitSleepItemLevels


class FitbitSleep(BaseModel):
    sleep: list[FitbitSleepItem]

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

    return svc_models.SleepData(
        start_time=datetime.datetime.strptime(
            main_sleep_item.startTime, DATETIME_FORMAT
        ),
        end_time=datetime.datetime.strptime(main_sleep_item.endTime, DATETIME_FORMAT),
        score=main_sleep_item.efficiency,
        sleep_minutes=main_sleep_item.duration / 60000
        - main_sleep_item.levels.summary.wake.minutes,
        wake_minutes=main_sleep_item.levels.summary.wake.minutes,
        slack_alias=slack_alias,
    )
