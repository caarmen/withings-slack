import dataclasses
import datetime
from typing import Optional

from pydantic import BaseModel, NonNegativeInt


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
    score: NonNegativeInt
    slack_alias: str
