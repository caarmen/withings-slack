import dataclasses
from enum import Enum, StrEnum, auto


class Ranking(Enum):
    ALL_TIME_TOP = auto()
    RECENT_TOP = auto()
    NONE = auto()


@dataclasses.dataclass
class Metric:
    value: int
    ranking: Ranking


class ActivityZone(StrEnum):
    PEAK = auto()
    CARDIO = auto()
    FAT_BURN = auto()
    OUT_OF_RANGE = auto()


@dataclasses.dataclass
class ActivityZoneMinutes:
    zone: ActivityZone
    minutes: Metric


@dataclasses.dataclass
class ActivityData:
    log_id: int
    type_id: int
    name: str
    total_minutes: Metric
    calories: Metric
    zone_minutes: list[ActivityZoneMinutes]


@dataclasses.dataclass
class ActivityHistory:
    latest_activity_data: ActivityData | None
    new_activity_data: ActivityData
