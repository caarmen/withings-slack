import dataclasses
import datetime
from typing import Optional

from pydantic import BaseModel, NonNegativeInt

from slackhealthbot.database.models import FitbitUser


@dataclasses.dataclass
class WeightData:
    weight_kg: float
    slack_alias: str
    last_weight_kg: Optional[float]


class SleepData(BaseModel):
    start_time: datetime.datetime
    end_time: datetime.datetime
    sleep_minutes: NonNegativeInt
    wake_minutes: NonNegativeInt


class ActivityZoneMinutes(BaseModel):
    name: str
    minutes: int


class ActivityData(BaseModel):
    log_id: int
    type_id: int
    name: str
    total_minutes: int
    calories: int
    zone_minutes: list[ActivityZoneMinutes]


def user_last_sleep_data(user: FitbitUser) -> Optional[SleepData]:
    return (
        SleepData(
            start_time=user.last_sleep_start_time,
            end_time=user.last_sleep_end_time,
            sleep_minutes=user.last_sleep_sleep_minutes,
            wake_minutes=user.last_sleep_wake_minutes,
        )
        if user.last_sleep_start_time
        else None
    )
