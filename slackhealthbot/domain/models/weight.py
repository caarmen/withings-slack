import dataclasses


@dataclasses.dataclass
class WeightData:
    weight_kg: float
    slack_alias: str
    last_weight_kg: float | None
