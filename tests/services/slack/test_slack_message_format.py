from withingsslack.services import slack
import pytest
import datetime


@pytest.mark.parametrize(
    "input,expected_output",
    [
        (55, "55m"),
        (65, "1h 5m"),
        (417, "6h 57m"),
        (721, "12h 1m"),
    ],
)
def test_format_minutes(input: int, expected_output: str):
    actual_output = slack.format_minutes(input)
    assert actual_output == expected_output


@pytest.mark.parametrize(
    "input,expected_output",
    [
        (datetime.datetime(2023, 5, 14, 1, 51, 33, 234), "1:51"),
        (datetime.datetime(2023, 5, 14, 15, 51, 33, 234), "15:51"),
    ],
)
def test_format_time(input: datetime.datetime, expected_output: str):
    actual_output = slack.format_time(input)
    assert actual_output == expected_output
