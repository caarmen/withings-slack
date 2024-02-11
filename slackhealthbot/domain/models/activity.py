import dataclasses
from enum import StrEnum, auto

from pydantic import BaseModel


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
