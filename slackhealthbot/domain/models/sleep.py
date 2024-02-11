import datetime

from pydantic import BaseModel, NonNegativeInt


class SleepData(BaseModel):
    start_time: datetime.datetime
    end_time: datetime.datetime
    sleep_minutes: NonNegativeInt
    wake_minutes: NonNegativeInt
