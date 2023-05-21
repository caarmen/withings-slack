import dataclasses
import datetime

from pydantic import BaseModel, NonNegativeInt


@dataclasses.dataclass
class WeightData:
    weight_kg: float
    slack_alias: str


class SleepData(BaseModel):
    start_time: datetime.datetime
    end_time: datetime.datetime
    sleep_minutes: NonNegativeInt
    wake_minutes: NonNegativeInt
    score: NonNegativeInt
    slack_alias: str
