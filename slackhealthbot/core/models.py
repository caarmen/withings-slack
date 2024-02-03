import dataclasses
import datetime
from enum import StrEnum, auto

from pydantic import BaseModel, NonNegativeInt


@dataclasses.dataclass
class WeightData:
    weight_kg: float
    slack_alias: str
    last_weight_kg: float | None


class SleepData(BaseModel):
    start_time: datetime.datetime
    end_time: datetime.datetime
    sleep_minutes: NonNegativeInt
    wake_minutes: NonNegativeInt


class ActivityZone(StrEnum):
    PEAK = auto()
    CARDIO = auto()
    FAT_BURN = auto()
    OUT_OF_RANGE = auto()


class ActivityZoneMinutes(BaseModel):
    zone: ActivityZone
    minutes: int


class ActivityData(BaseModel):
    log_id: int
    type_id: int
    name: str
    total_minutes: int
    calories: int
    zone_minutes: list[ActivityZoneMinutes]


@dataclasses.dataclass
class ActivityHistory:
    latest_activity_data: ActivityData | None
    new_activity_data: ActivityData


@dataclasses.dataclass
class OAuthFields:
    oauth_userid: str
    oauth_access_token: str
    oauth_refresh_token: str
    oauth_expiration_date: datetime
