import datetime as dt
from types import ModuleType
from typing import Any
from zoneinfo import ZoneInfo

import pytest


def freeze_time(
    mp: pytest.MonkeyPatch,
    dt_module_to_freeze: ModuleType,
    frozen_datetime_args: tuple[Any],
    local_timezone: ZoneInfo = ZoneInfo("UTC"),
):
    class FrozenDate(dt.datetime):
        def now(tz):
            return FrozenDate(*frozen_datetime_args, tzinfo=tz)

        def astimezone(self):
            return super().astimezone(tz=local_timezone)

    mp.setattr(dt_module_to_freeze, "datetime", FrozenDate)
