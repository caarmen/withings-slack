import datetime
import os
from pathlib import Path

import pytest

from slackhealthbot.services.fitbit.parser import parse_sleep
from slackhealthbot.services.models import SleepData


@pytest.mark.parametrize(
    "input_filename,expected_sleep_data",
    [
        (
            "fitbit_sleep_response_1_item.json",
            SleepData(
                start_time=datetime.datetime(2023, 5, 13, 0, 40, 0),
                end_time=datetime.datetime(2023, 5, 13, 9, 27, 30),
                sleep_minutes=465,
                wake_minutes=62,
                score=95,
                slack_alias="somebody",
            ),
        ),
        (
            "fitbit_sleep_response_2_items.json",
            SleepData(
                start_time=datetime.datetime(2023, 5, 14, 1, 51, 0),
                end_time=datetime.datetime(2023, 5, 14, 9, 23, 30),
                sleep_minutes=417,
                wake_minutes=35,
                score=98,
                slack_alias="somebody",
            ),
        ),
        (
            "fitbit_sleep_response_classic.json",
            SleepData(
                start_time=datetime.datetime(2023, 5, 17, 0, 35, 0),
                end_time=datetime.datetime(2023, 5, 17, 8, 7, 30),
                sleep_minutes=439,
                wake_minutes=2,
                score=97,
                slack_alias="somebody",
            ),
        ),
        ("fitbit_sleep_response_no_main_sleep_item.json", None),
    ],
)
def test_parse_sleep(input_filename: str, expected_sleep_data: SleepData):
    input_file = (
        Path(os.path.abspath(__file__)).parent.parent.parent / "data" / input_filename
    )
    with open(input_file) as input:
        actual_sleep_data = parse_sleep(input=input.read(), slack_alias="somebody")
        assert actual_sleep_data == expected_sleep_data
