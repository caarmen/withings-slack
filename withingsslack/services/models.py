import dataclasses


@dataclasses.dataclass
class WeightData:
    weight_kg: float
    slack_alias: str


@dataclasses.dataclass
class SleepData:
    total_sleep_minutes: int
    deep_minutes: int
    light_minutes: int
    rem_minutes: int
    wake_minutes: int
    slack_alias: str
