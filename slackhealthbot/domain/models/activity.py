import dataclasses
from enum import StrEnum, auto


class ActivityZone(StrEnum):
    PEAK = auto()
    CARDIO = auto()
    FAT_BURN = auto()
    OUT_OF_RANGE = auto()


@dataclasses.dataclass
class ActivityZoneMinutes:
    zone: ActivityZone
    minutes: int


@dataclasses.dataclass
class ActivityData:
    log_id: int
    type_id: int
    total_minutes: int
    calories: int
    zone_minutes: list[ActivityZoneMinutes]


@dataclasses.dataclass
class TopActivityStats:
    top_calories: int | None
    top_total_minutes: int | None
    top_zone_minutes: list[ActivityZoneMinutes]


@dataclasses.dataclass
class ActivityHistory:
    latest_activity_data: ActivityData | None
    new_activity_data: ActivityData
    all_time_top_activity_data: TopActivityStats
    recent_top_activity_data: TopActivityStats
