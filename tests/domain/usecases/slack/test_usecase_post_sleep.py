import dataclasses
import datetime
import re

import pytest

from slackhealthbot.domain.models.sleep import SleepData
from slackhealthbot.domain.usecases.slack import usecase_post_sleep


@pytest.mark.parametrize(
    "input_minutes,expected_output",
    [
        (55, "55m"),
        (65, "1h 5m"),
        (417, "6h 57m"),
        (721, "12h 1m"),
    ],
)
def test_format_minutes(input_minutes: int, expected_output: str):
    actual_output = usecase_post_sleep.format_minutes(input_minutes)
    assert actual_output == expected_output


@pytest.mark.parametrize(
    "input_datetime,expected_output",
    [
        (datetime.datetime(2023, 5, 14, 1, 51, 33, 234), "1:51"),
        (datetime.datetime(2023, 5, 14, 15, 51, 33, 234), "15:51"),
    ],
)
def test_format_time(input_datetime: datetime.datetime, expected_output: str):
    actual_output = usecase_post_sleep.format_time(input_datetime)
    assert actual_output == expected_output


@dataclasses.dataclass
class CreateMessageScenario:
    name: str
    new_sleep_data: SleepData
    last_sleep_data: SleepData
    expected_message_regex: str


CREATE_MESSAGE_SCENARIOS = [
    CreateMessageScenario(
        name="almost no change",
        new_sleep_data=SleepData(
            start_time=datetime.datetime(1999, 12, 31, 23, 42, 22),
            end_time=datetime.datetime(2000, 1, 1, 10, 14, 9),
            sleep_minutes=600,
            wake_minutes=5,
        ),
        last_sleep_data=SleepData(
            start_time=datetime.datetime(1999, 12, 30, 23, 42, 20),
            end_time=datetime.datetime(1999, 12, 31, 10, 14, 10),
            sleep_minutes=601,
            wake_minutes=4,
        ),
        expected_message_regex="^.*➡️.*➡️.*➡️.*➡️.*$",
    ),
    CreateMessageScenario(
        name="big decrease",
        new_sleep_data=SleepData(
            start_time=datetime.datetime(1999, 12, 31, 23, 42, 22),
            end_time=datetime.datetime(2000, 1, 1, 10, 14, 9),
            sleep_minutes=600,
            wake_minutes=1,
        ),
        last_sleep_data=SleepData(
            start_time=datetime.datetime(1999, 12, 31, 1, 42, 20),
            end_time=datetime.datetime(1999, 12, 31, 13, 14, 10),
            sleep_minutes=800,
            wake_minutes=120,
        ),
        expected_message_regex="^.*⬇️.*⬇️.*⬇️.*⬇️.*$",
    ),
    CreateMessageScenario(
        name="slight decrease",
        new_sleep_data=SleepData(
            start_time=datetime.datetime(1999, 12, 31, 23, 42, 22),
            end_time=datetime.datetime(2000, 1, 1, 10, 14, 9),
            sleep_minutes=600,
            wake_minutes=1,
        ),
        last_sleep_data=SleepData(
            start_time=datetime.datetime(1999, 12, 31, 0, 15, 20),
            end_time=datetime.datetime(1999, 12, 31, 10, 30, 10),
            sleep_minutes=640,
            wake_minutes=40,
        ),
        expected_message_regex="^.*↘️.*↘️.*↘️.*↘️.*$",
    ),
    CreateMessageScenario(
        name="big increase",
        new_sleep_data=SleepData(
            start_time=datetime.datetime(1999, 12, 31, 23, 42, 22),
            end_time=datetime.datetime(2000, 1, 1, 10, 14, 9),
            sleep_minutes=600,
            wake_minutes=100,
        ),
        last_sleep_data=SleepData(
            start_time=datetime.datetime(1999, 12, 30, 18, 42, 20),
            end_time=datetime.datetime(1999, 12, 31, 6, 14, 10),
            sleep_minutes=401,
            wake_minutes=1,
        ),
        expected_message_regex="^.*⬆️.*⬆️.*⬆️.*⬆️.*$",
    ),
    CreateMessageScenario(
        name="slight increase",
        new_sleep_data=SleepData(
            start_time=datetime.datetime(1999, 12, 31, 23, 42, 22),
            end_time=datetime.datetime(2000, 1, 1, 10, 14, 9),
            sleep_minutes=600,
            wake_minutes=100,
        ),
        last_sleep_data=SleepData(
            start_time=datetime.datetime(1999, 12, 30, 23, 0, 20),
            end_time=datetime.datetime(1999, 12, 31, 9, 50, 10),
            sleep_minutes=560,
            wake_minutes=60,
        ),
        expected_message_regex="^.*↗️.*↗️.*↗️.*↗️.*$",
    ),
    CreateMessageScenario(
        name="mixed increase and decrease",
        new_sleep_data=SleepData(
            start_time=datetime.datetime(1999, 12, 31, 23, 42, 22),
            end_time=datetime.datetime(2000, 1, 1, 10, 14, 9),
            sleep_minutes=600,
            wake_minutes=100,
        ),
        last_sleep_data=SleepData(
            start_time=datetime.datetime(1999, 12, 30, 23, 0, 20),
            end_time=datetime.datetime(1999, 12, 31, 8, 50, 10),
            sleep_minutes=620,
            wake_minutes=150,
        ),
        expected_message_regex="^.*↗️.*⬆️.*↘️.*⬇️.*$",
    ),
]


@pytest.mark.parametrize(
    ids=[x.name for x in CREATE_MESSAGE_SCENARIOS],
    argnames=["scenario"],
    argvalues=[[x] for x in CREATE_MESSAGE_SCENARIOS],
)
def test_create_message(scenario: CreateMessageScenario):
    actual_message = usecase_post_sleep.create_message(
        slack_alias="somebody",
        new_sleep_data=scenario.new_sleep_data,
        last_sleep_data=scenario.last_sleep_data,
    )
    assert re.search(scenario.expected_message_regex, actual_message.replace("\n", ""))
