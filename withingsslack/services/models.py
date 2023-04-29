import dataclasses
from datetime import datetime


@dataclasses.dataclass
class WeightData:
    weight_kg: float
    date: datetime
    slack_alias: str
