import dataclasses
import re

import pytest

from slackhealthbot.domain.models.activity import (
    ActivityData,
    ActivityHistory,
    ActivityZone,
    ActivityZoneMinutes,
)
from slackhealthbot.domain.usecases.slack import usecase_post_activity


@pytest.mark.parametrize(
    [
        "input_value",
        "expected_output",
    ],
    [
        (0, "➡️"),
        (1, "➡️"),
        (-1, "➡️"),
        (100, "⬆️"),
        (-100, "⬇️"),
        (5, "↗️"),
        (-5, "↘️"),
    ],
)
def test_get_activity_minutes_change_icon(
    input_value: int,
    expected_output: str,
):
    actual_output = usecase_post_activity.get_activity_minutes_change_icon(input_value)
    assert actual_output == expected_output


@pytest.mark.parametrize(
    [
        "input_value",
        "expected_output",
    ],
    [
        (0, "➡️"),
        (1, "➡️"),
        (-1, "➡️"),
        (100, "⬆️"),
        (-100, "⬇️"),
        (35, "↗️"),
        (-35, "↘️"),
    ],
)
def test_get_activity_calories_change_icon(
    input_value: int,
    expected_output: str,
):
    actual_output = usecase_post_activity.get_activity_calories_change_icon(input_value)
    assert actual_output == expected_output


@pytest.mark.parametrize(
    [
        "input_value",
        "input_all_time_top_value",
        "input_recent_top_value",
        "expected_output",
    ],
    [
        (12, 14, 13, ""),
        (13, 14, 13, "New record (last 2 days)! 🏆"),
        (13, 13, 13, "New all-time record! 🏆"),
    ],
)
def test_get_ranking_text(
    input_value: int,
    input_all_time_top_value: int,
    input_recent_top_value: int,
    expected_output: str,
):
    actual_output = usecase_post_activity.get_ranking_text(
        input_value,
        input_all_time_top_value,
        input_recent_top_value,
        record_history_days=2,
    )
    assert actual_output == expected_output


@dataclasses.dataclass
class CreateMessageScenario:
    name: str
    new_activity_data: ActivityData
    expected_message_regex: str


CREATE_MESSAGE_SCENARIOS = [
    CreateMessageScenario(
        name="new all-time record",
        new_activity_data=ActivityData(
            log_id=-3,
            type_id=123,
            name="Dancing",
            total_minutes=120,
            calories=315,
            zone_minutes=[
                ActivityZoneMinutes(
                    zone=ActivityZone.CARDIO,
                    minutes=120,
                ),
                ActivityZoneMinutes(
                    zone=ActivityZone.FAT_BURN,
                    minutes=60,
                ),
            ],
        ),
        expected_message_regex="^.* ⬆️ New all-time record! 🏆.* ⬆️ New all-time record! 🏆.* ⬆️ New all-time record! "
        "🏆.* ⬆️ New all-time record! 🏆$",
    ),
    CreateMessageScenario(
        name="recent top record",
        new_activity_data=ActivityData(
            log_id=-3,
            type_id=123,
            name="Dancing",
            total_minutes=90,
            calories=175,
            zone_minutes=[
                ActivityZoneMinutes(
                    zone=ActivityZone.CARDIO,
                    minutes=50,
                ),
                ActivityZoneMinutes(
                    zone=ActivityZone.FAT_BURN,
                    minutes=25,
                ),
            ],
        ),
        expected_message_regex="^.* ⬆️ New record \\(last 30 days\\)! 🏆.* ➡️ New record \\(last 30 days\\)! 🏆.* ⬆️ New "
        "record \\(last 30 days\\)! 🏆.* ➡️ New record \\(last 30 days\\)! 🏆$",
    ),
    CreateMessageScenario(
        name="lowest score",
        new_activity_data=ActivityData(
            log_id=-3,
            type_id=123,
            name="Dancing",
            total_minutes=1,
            calories=1,
            zone_minutes=[
                ActivityZoneMinutes(
                    zone=ActivityZone.CARDIO,
                    minutes=1,
                ),
                ActivityZoneMinutes(
                    zone=ActivityZone.FAT_BURN,
                    minutes=1,
                ),
            ],
        ),
        expected_message_regex="^.* ⬇️ .* ⬇️ .* ⬇️ .* ⬇️ $",
    ),
]


@pytest.mark.parametrize(
    ids=[x.name for x in CREATE_MESSAGE_SCENARIOS],
    argnames=["scenario"],
    argvalues=[[x] for x in CREATE_MESSAGE_SCENARIOS],
)
def test_create_message(scenario: CreateMessageScenario):
    activity_history = ActivityHistory(
        new_activity_data=scenario.new_activity_data,
        latest_activity_data=ActivityData(
            log_id=-1,
            type_id=123,
            name="Dancing",
            total_minutes=15,
            calories=150,
            zone_minutes=[
                ActivityZoneMinutes(
                    zone=ActivityZone.CARDIO,
                    minutes=15,
                ),
                ActivityZoneMinutes(
                    zone=ActivityZone.FAT_BURN,
                    minutes=24,
                ),
            ],
        ),
        all_time_top_activity_data=ActivityData(
            log_id=-3,
            type_id=123,
            name="Dancing",
            total_minutes=100,
            calories=215,
            zone_minutes=[
                ActivityZoneMinutes(
                    zone=ActivityZone.CARDIO,
                    minutes=60,
                ),
                ActivityZoneMinutes(
                    zone=ActivityZone.FAT_BURN,
                    minutes=40,
                ),
            ],
        ),
        recent_top_activity_data=ActivityData(
            log_id=-4,
            type_id=123,
            name="Dancing",
            total_minutes=90,
            calories=175,
            zone_minutes=[
                ActivityZoneMinutes(
                    zone=ActivityZone.CARDIO,
                    minutes=50,
                ),
                ActivityZoneMinutes(
                    zone=ActivityZone.FAT_BURN,
                    minutes=25,
                ),
            ],
        ),
    )
    actual_message = usecase_post_activity.create_message(
        slack_alias="somebody",
        activity_history=activity_history,
        record_history_days=30,
    )
    assert re.search(scenario.expected_message_regex, actual_message.replace("\n", ""))
