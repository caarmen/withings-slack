import dataclasses
import datetime
from typing import Any

from slackhealthbot.data.repositories.fitbitrepository import Sleep


@dataclasses.dataclass
class FitbitSleepScenario:
    input_initial_sleep_data: dict[str, int | None]
    input_mock_fitbit_response: dict[str, Any]
    expected_new_last_sleep_data: Sleep
    expected_icons: str | None


sleep_scenarios: dict[str, FitbitSleepScenario] = {
    "No previous sleep data": FitbitSleepScenario(
        # No previous sleep data
        input_initial_sleep_data={
            "last_sleep_start_time": None,
            "last_sleep_end_time": None,
            "last_sleep_sleep_minutes": None,
            "last_sleep_wake_minutes": None,
        },
        input_mock_fitbit_response={
            "sleep": [
                {
                    "endTime": "2023-05-13T09:27:30.000",
                    "duration": 31620000,
                    "startTime": "2023-05-13T00:40:00.000",
                    "type": "stages",
                    "isMainSleep": True,
                    "levels": {
                        "summary": {"wake": {"minutes": 32}},
                    },
                },
            ]
        },
        expected_new_last_sleep_data=Sleep(
            start_time=datetime.datetime(2023, 5, 13, 0, 40, 0),
            end_time=datetime.datetime(2023, 5, 13, 9, 27, 30),
            sleep_minutes=495,
            wake_minutes=32,
        ),
        expected_icons="",
    ),
    "New sleep data higher": FitbitSleepScenario(
        # Previous sleep data exists.
        # Newer values are all higher than previous values
        input_initial_sleep_data={
            "last_sleep_start_time": datetime.datetime(2023, 5, 11, 23, 39, 0),
            "last_sleep_end_time": datetime.datetime(2023, 5, 12, 8, 28, 0),
            "last_sleep_sleep_minutes": 449,
            "last_sleep_wake_minutes": 80,
        },
        input_mock_fitbit_response={
            "sleep": [
                {
                    "startTime": "2023-05-13T00:40:00.000",
                    "endTime": "2023-05-13T09:27:30.000",
                    "duration": 31620000,
                    "type": "classic",
                    "isMainSleep": True,
                    "levels": {
                        "summary": {
                            "asleep": {"minutes": 495},
                            "awake": {"minutes": 130},
                        },
                    },
                },
            ]
        },
        expected_new_last_sleep_data=Sleep(
            start_time=datetime.datetime(2023, 5, 13, 0, 40, 0),
            end_time=datetime.datetime(2023, 5, 13, 9, 27, 30),
            sleep_minutes=495,
            wake_minutes=130,
        ),
        expected_icons="⬆️.*⬆️.*⬆️.*⬆️",
    ),
    "New sleep data slightly higher": FitbitSleepScenario(
        # Previous sleep data exists.
        # Newer values are all slightly higher than previous values
        input_initial_sleep_data={
            "last_sleep_start_time": datetime.datetime(2023, 5, 12, 0, 5, 0),
            "last_sleep_end_time": datetime.datetime(2023, 5, 12, 9, 0, 0),
            "last_sleep_sleep_minutes": 460,
            "last_sleep_wake_minutes": 16,
        },
        input_mock_fitbit_response={
            "sleep": [
                {
                    "startTime": "2023-05-13T00:40:00.000",
                    "endTime": "2023-05-13T09:27:30.000",
                    "duration": 32700000,
                    "type": "stages",
                    "isMainSleep": True,
                    "levels": {
                        "summary": {"wake": {"minutes": 50}},
                    },
                },
            ]
        },
        expected_new_last_sleep_data=Sleep(
            start_time=datetime.datetime(2023, 5, 13, 0, 40, 0),
            end_time=datetime.datetime(2023, 5, 13, 9, 27, 30),
            sleep_minutes=495,
            wake_minutes=50,
        ),
        expected_icons="↗️.*↗️.*↗️.*↗️",
    ),
    "New sleep data barely higher": FitbitSleepScenario(
        # Previous sleep data exists.
        # Newer values are all barely higher than previous values
        input_initial_sleep_data={
            "last_sleep_start_time": datetime.datetime(2023, 5, 12, 0, 39, 0),
            "last_sleep_end_time": datetime.datetime(2023, 5, 12, 9, 25, 0),
            "last_sleep_sleep_minutes": 490,
            "last_sleep_wake_minutes": 45,
        },
        input_mock_fitbit_response={
            "sleep": [
                {
                    "startTime": "2023-05-13T00:40:00.000",
                    "endTime": "2023-05-13T09:27:30.000",
                    "duration": 31620000,
                    "type": "classic",
                    "isMainSleep": True,
                    "levels": {
                        "summary": {
                            "asleep": {"minutes": 495},
                            "awake": {"minutes": 50},
                        },
                    },
                },
            ]
        },
        expected_new_last_sleep_data=Sleep(
            start_time=datetime.datetime(2023, 5, 13, 0, 40, 0),
            end_time=datetime.datetime(2023, 5, 13, 9, 27, 30),
            sleep_minutes=495,
            wake_minutes=50,
        ),
        expected_icons="➡️.*➡️.*➡️.*➡️",
    ),
    "New sleep data barely lower": FitbitSleepScenario(
        # Previous sleep data exists.
        # Newer values are all barely lower than previous values
        input_initial_sleep_data={
            "last_sleep_start_time": datetime.datetime(2023, 5, 12, 0, 41, 0),
            "last_sleep_end_time": datetime.datetime(2023, 5, 12, 9, 28, 0),
            "last_sleep_sleep_minutes": 500,
            "last_sleep_wake_minutes": 51,
        },
        input_mock_fitbit_response={
            "sleep": [
                {
                    "startTime": "2023-05-13T00:40:00.000",
                    "endTime": "2023-05-13T09:27:30.000",
                    "duration": 31620000,
                    "type": "classic",
                    "isMainSleep": True,
                    "levels": {
                        "summary": {
                            "asleep": {"minutes": 495},
                            "awake": {"minutes": 50},
                        },
                    },
                },
            ]
        },
        expected_new_last_sleep_data=Sleep(
            start_time=datetime.datetime(2023, 5, 13, 0, 40, 0),
            end_time=datetime.datetime(2023, 5, 13, 9, 27, 30),
            sleep_minutes=495,
            wake_minutes=50,
        ),
        expected_icons="➡️.*➡️.*➡️.*➡️",
    ),
    "New sleep data slightly lower": FitbitSleepScenario(
        # Previous sleep data exists.
        # Newer values are all slightly lower than previous values
        input_initial_sleep_data={
            "last_sleep_start_time": datetime.datetime(2023, 5, 12, 1, 15, 0),
            "last_sleep_end_time": datetime.datetime(2023, 5, 12, 10, 11, 0),
            "last_sleep_sleep_minutes": 539,
            "last_sleep_wake_minutes": 80,
        },
        input_mock_fitbit_response={
            "sleep": [
                {
                    "startTime": "2023-05-13T00:40:00.000",
                    "endTime": "2023-05-13T09:27:30.000",
                    "duration": 31620000,
                    "type": "classic",
                    "isMainSleep": True,
                    "levels": {
                        "summary": {
                            "asleep": {"minutes": 495},
                            "awake": {"minutes": 50},
                        },
                    },
                },
            ]
        },
        expected_new_last_sleep_data=Sleep(
            start_time=datetime.datetime(2023, 5, 13, 0, 40, 0),
            end_time=datetime.datetime(2023, 5, 13, 9, 27, 30),
            sleep_minutes=495,
            wake_minutes=50,
        ),
        expected_icons="↘️.*↘️.*↘️.*↘️",
    ),
    "New sleep data lower": FitbitSleepScenario(
        # Previous sleep data exists.
        # Newer values are all lower than previous values
        input_initial_sleep_data={
            "last_sleep_start_time": datetime.datetime(2023, 5, 12, 1, 41, 0),
            "last_sleep_end_time": datetime.datetime(2023, 5, 12, 10, 28, 0),
            "last_sleep_sleep_minutes": 560,
            "last_sleep_wake_minutes": 200,
        },
        input_mock_fitbit_response={
            "sleep": [
                {
                    "startTime": "2023-05-13T00:40:00.000",
                    "endTime": "2023-05-13T09:27:30.000",
                    "duration": 31620000,
                    "type": "classic",
                    "isMainSleep": True,
                    "levels": {
                        "summary": {
                            "asleep": {"minutes": 495},
                            "awake": {"minutes": 130},
                        },
                    },
                },
            ]
        },
        expected_new_last_sleep_data=Sleep(
            start_time=datetime.datetime(2023, 5, 13, 0, 40, 0),
            end_time=datetime.datetime(2023, 5, 13, 9, 27, 30),
            sleep_minutes=495,
            wake_minutes=130,
        ),
        expected_icons="⬇️.*⬇️.*⬇️.*⬇️",
    ),
    "Invalid json response": FitbitSleepScenario(
        input_initial_sleep_data={
            "last_sleep_start_time": datetime.datetime(2023, 5, 12, 1, 41, 0),
            "last_sleep_end_time": datetime.datetime(2023, 5, 12, 10, 28, 0),
            "last_sleep_sleep_minutes": 560,
            "last_sleep_wake_minutes": 200,
        },
        input_mock_fitbit_response={"foo": "bar"},
        expected_new_last_sleep_data=Sleep(
            start_time=datetime.datetime(2023, 5, 12, 1, 41, 0),
            end_time=datetime.datetime(2023, 5, 12, 10, 28, 0),
            sleep_minutes=560,
            wake_minutes=200,
        ),
        expected_icons=None,
    ),
}


@dataclasses.dataclass
class FitbitActivityScenario:
    input_initial_activity_data: dict[str, int | datetime.datetime] | None
    input_mock_fitbit_response: dict[str, Any]
    expected_new_last_activity_log_id: int
    expected_message_pattern: str | None

    @property
    def is_new_log_expected(self) -> bool:
        return bool(self.expected_message_pattern)


activity_scenarios: dict[str, FitbitActivityScenario] = {
    "No previous activity data, new Spinning activity": FitbitActivityScenario(
        input_initial_activity_data=None,
        input_mock_fitbit_response={
            "activities": [
                {
                    "activeZoneMinutes": {
                        "minutesInHeartRateZones": [
                            {
                                "minutes": 8,
                                "type": "FAT_BURN",
                            },
                            {
                                "minutes": 0,
                                "type": "CARDIO",
                            },
                            {
                                "minutes": 0,
                                "type": "OUT_OF_RANGE",
                            },
                            {
                                "minutes": 0,
                                "type": "PEAK",
                            },
                        ]
                    },
                    "activityName": "Spinning",
                    "activityTypeId": 55001,
                    "logId": 1234,
                    "calories": 76,
                    "duration": 665000,
                },
            ]
        },
        expected_new_last_activity_log_id=1234,
        expected_message_pattern="New Spinning activity.*Fat burn.*8.*New all-time record",
    ),
    "New Spinning activity, partial zones": FitbitActivityScenario(
        input_initial_activity_data={
            "log_id": 1234,
            "total_minutes": 30,
            "calories": 10,
            "fat_burn_minutes": 7,
            "cardio_minutes": 13,
            "created_at": datetime.datetime(1999, 12, 31, 0, 0, 0),
            "updated_at": datetime.datetime(1999, 12, 31, 0, 0, 0),
        },
        input_mock_fitbit_response={
            "activities": [
                {
                    "activeZoneMinutes": {
                        "minutesInHeartRateZones": [
                            {
                                "minutes": 8,
                                "type": "FAT_BURN",
                            },
                            {
                                "minutes": 9,
                                "type": "CARDIO",
                            },
                            {
                                "minutes": 0,
                                "type": "OUT_OF_RANGE",
                            },
                            {
                                "minutes": 0,
                                "type": "PEAK",
                            },
                        ]
                    },
                    "activityName": "Spinning",
                    "activityTypeId": 55001,
                    "logId": 1235,
                    "calories": 76,
                    "duration": 665000,
                },
            ]
        },
        expected_new_last_activity_log_id=1235,
        expected_message_pattern=(
            "New Spinning activity.*⬇️ New record.*⬆️ New all-time record.*Fat burn.*8.*➡.*New all-time "
            "record.*Cardio.*9.*↘️ New record"
        ),
    ),
    "New Spinning activity, full zones": FitbitActivityScenario(
        input_initial_activity_data={
            "log_id": 1234,
            "total_minutes": 8,
            "calories": 70,
            "fat_burn_minutes": 1,
            "cardio_minutes": 20,
            "out_of_range_minutes": None,
            "peak_minutes": None,
            "created_at": datetime.datetime(1999, 12, 31, 0, 0, 0),
            "updated_at": datetime.datetime(1999, 12, 31, 0, 0, 0),
        },
        input_mock_fitbit_response={
            "activities": [
                {
                    "activeZoneMinutes": {
                        "minutesInHeartRateZones": [
                            {
                                "minutes": 12,
                                "type": "FAT_BURN",
                            },
                            {
                                "minutes": 9,
                                "type": "CARDIO",
                            },
                            {
                                "minutes": 10,
                                "type": "OUT_OF_RANGE",
                            },
                            {
                                "minutes": 11,
                                "type": "PEAK",
                            },
                        ]
                    },
                    "activityName": "Spinning",
                    "activityTypeId": 55001,
                    "logId": 1235,
                    "calories": 76,
                    "duration": 665000,
                },
            ]
        },
        expected_new_last_activity_log_id=1235,
        expected_message_pattern="New Spinning activity.*↗️ New all-time record.*➡️ New all-time record.*"
        + "Fat burn.*12.*⬆️ New all-time record.*Cardio.*9.*⬇️ New record.*Out of range.*10.*↗️.*Peak.*11.*⬆️ New "
        "all-time record",
    ),
    "New unrecognized activity": FitbitActivityScenario(
        input_initial_activity_data={
            "log_id": 1234,
            "calories": 70,
            "fat_burn_minutes": 1,
            "cardio_minutes": 20,
            "out_of_range_minutes": None,
            "peak_minutes": None,
            "created_at": datetime.datetime(1999, 12, 31, 0, 0, 0),
            "updated_at": datetime.datetime(1999, 12, 31, 0, 0, 0),
        },
        input_mock_fitbit_response={
            "activities": [
                {
                    "activeZoneMinutes": {
                        "minutesInHeartRateZones": [
                            {
                                "minutes": 8,
                                "type": "FAT_BURN",
                            },
                            {
                                "minutes": 9,
                                "type": "CARDIO",
                            },
                            {
                                "minutes": 0,
                                "type": "OUT_OF_RANGE",
                            },
                            {
                                "minutes": 0,
                                "type": "PEAK",
                            },
                        ]
                    },
                    "activityName": "Glandating",
                    "activityTypeId": 4242,
                    "logId": 1235,
                    "calories": 76,
                    "duration": 665000,
                },
            ]
        },
        expected_new_last_activity_log_id=1234,
        expected_message_pattern=None,
    ),
    "Invalid json response": FitbitActivityScenario(
        input_initial_activity_data={
            "log_id": 1234,
            "calories": 70,
            "fat_burn_minutes": 1,
            "cardio_minutes": 20,
            "out_of_range_minutes": None,
            "peak_minutes": None,
            "created_at": datetime.datetime(1999, 12, 31, 0, 0, 0),
            "updated_at": datetime.datetime(1999, 12, 31, 0, 0, 0),
        },
        input_mock_fitbit_response={"foo": "bar"},
        expected_new_last_activity_log_id=1234,
        expected_message_pattern=None,
    ),
}
