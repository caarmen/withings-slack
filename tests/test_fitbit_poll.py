import datetime
import json
import re

import pytest
from requests_mock.mocker import Mocker

from slackhealthbot.database.models import User
from slackhealthbot.scheduler import Cache, do_poll
from slackhealthbot.services.models import SleepData, user_last_sleep_data
from slackhealthbot.settings import settings
from tests.factories.factories import FitbitUserFactory, UserFactory


@pytest.mark.parametrize(
    ids=[
        "No previous sleep data",
        "New sleep data higher",
        "New sleep data slightly higher",
        "New sleep data barely higher",
        "New sleep data barely lower",
        "New sleep data slightly lower",
        "New sleep data lower",
    ],
    argnames="input_initial_sleep_data, "
    "input_mock_fitbit_response, "
    "expected_new_last_sleep_data, "
    "expected_icons",
    argvalues=[
        (
            # No previous sleep data
            {},
            {
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
            SleepData(
                start_time=datetime.datetime(2023, 5, 13, 0, 40, 0),
                end_time=datetime.datetime(2023, 5, 13, 9, 27, 30),
                sleep_minutes=495,
                wake_minutes=32,
            ),
            "",
        ),
        (
            # Previous sleep data exists.
            # Newer values are all higher than previous values
            {
                "last_sleep_start_time": datetime.datetime(2023, 5, 11, 23, 39, 0),
                "last_sleep_end_time": datetime.datetime(2023, 5, 12, 8, 28, 0),
                "last_sleep_sleep_minutes": 449,
                "last_sleep_wake_minutes": 80,
            },
            {
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
            SleepData(
                start_time=datetime.datetime(2023, 5, 13, 0, 40, 0),
                end_time=datetime.datetime(2023, 5, 13, 9, 27, 30),
                sleep_minutes=495,
                wake_minutes=130,
            ),
            "⬆️.*⬆️.*⬆️.*⬆️",
        ),
        (
            # Previous sleep data exists.
            # Newer values are all slightly higher than previous values
            {
                "last_sleep_start_time": datetime.datetime(2023, 5, 12, 0, 5, 0),
                "last_sleep_end_time": datetime.datetime(2023, 5, 12, 9, 0, 0),
                "last_sleep_sleep_minutes": 460,
                "last_sleep_wake_minutes": 16,
            },
            {
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
            SleepData(
                start_time=datetime.datetime(2023, 5, 13, 0, 40, 0),
                end_time=datetime.datetime(2023, 5, 13, 9, 27, 30),
                sleep_minutes=495,
                wake_minutes=50,
            ),
            "↗️.*↗️.*↗️.*↗️",
        ),
        (
            # Previous sleep data exists.
            # Newer values are all barely higher than previous values
            {
                "last_sleep_start_time": datetime.datetime(2023, 5, 12, 0, 39, 0),
                "last_sleep_end_time": datetime.datetime(2023, 5, 12, 9, 25, 0),
                "last_sleep_sleep_minutes": 490,
                "last_sleep_wake_minutes": 45,
            },
            {
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
            SleepData(
                start_time=datetime.datetime(2023, 5, 13, 0, 40, 0),
                end_time=datetime.datetime(2023, 5, 13, 9, 27, 30),
                sleep_minutes=495,
                wake_minutes=50,
            ),
            "➡️.*➡️.*➡️.*➡️",
        ),
        (
            # Previous sleep data exists.
            # Newer values are all barely lower than previous values
            {
                "last_sleep_start_time": datetime.datetime(2023, 5, 12, 0, 41, 0),
                "last_sleep_end_time": datetime.datetime(2023, 5, 12, 9, 28, 0),
                "last_sleep_sleep_minutes": 500,
                "last_sleep_wake_minutes": 51,
            },
            {
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
            SleepData(
                start_time=datetime.datetime(2023, 5, 13, 0, 40, 0),
                end_time=datetime.datetime(2023, 5, 13, 9, 27, 30),
                sleep_minutes=495,
                wake_minutes=50,
            ),
            "➡️.*➡️.*➡️.*➡️",
        ),
        (
            # Previous sleep data exists.
            # Newer values are all slightly lower than previous values
            {
                "last_sleep_start_time": datetime.datetime(2023, 5, 12, 1, 15, 0),
                "last_sleep_end_time": datetime.datetime(2023, 5, 12, 10, 11, 0),
                "last_sleep_sleep_minutes": 539,
                "last_sleep_wake_minutes": 80,
            },
            {
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
            SleepData(
                start_time=datetime.datetime(2023, 5, 13, 0, 40, 0),
                end_time=datetime.datetime(2023, 5, 13, 9, 27, 30),
                sleep_minutes=495,
                wake_minutes=50,
            ),
            "↘️.*↘️.*↘️.*↘️",
        ),
        (
            # Previous sleep data exists.
            # Newer values are all lower than previous values
            {
                "last_sleep_start_time": datetime.datetime(2023, 5, 12, 1, 41, 0),
                "last_sleep_end_time": datetime.datetime(2023, 5, 12, 10, 28, 0),
                "last_sleep_sleep_minutes": 560,
                "last_sleep_wake_minutes": 200,
            },
            {
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
            SleepData(
                start_time=datetime.datetime(2023, 5, 13, 0, 40, 0),
                end_time=datetime.datetime(2023, 5, 13, 9, 27, 30),
                sleep_minutes=495,
                wake_minutes=130,
            ),
            "⬇️.*⬇️.*⬇️.*⬇️",
        ),
    ],
)
def test_fitbit_poll(
    mocked_session,
    requests_mock: Mocker,
    user_factory: UserFactory,
    fitbit_user_factory: FitbitUserFactory,
    input_initial_sleep_data,
    input_mock_fitbit_response,
    expected_new_last_sleep_data,
    expected_icons,
):
    """
    Given a user with given previous sleep data logged
    When we poll fitbit to get new sleep data
    Then the last sleep is updated in the database
    And the message is posted to slack with the correct icon.
    """

    # Given a user with the given previous sleep data
    user: User = user_factory(fitbit=None)
    fitbit_user_factory(
        user_id=user.id,
        **input_initial_sleep_data,
        oauth_expiration_date=datetime.datetime.utcnow() + datetime.timedelta(days=1),
    )

    # Mock fitbit endpoint to return some sleep data
    requests_mock.get(
        url=f"{settings.fitbit_base_url}1.2/user/-/sleep/date/2023-01-23.json",
        json=input_mock_fitbit_response,
    )

    # Verify we call the slack post with the expected request data
    def slack_post_matcher(request):
        actual_message = json.loads(request.text)["text"].replace("\n", "")
        assert re.search(expected_icons, actual_message)
        return True

    # Mock an empty ok response from the slack webhook
    requests_mock.post(
        url=f"{settings.slack_webhook_url}",
        status_code=200,
        additional_matcher=slack_post_matcher,
    )

    # When we poll for new sleep data
    do_poll(db=mocked_session, cache=Cache(), when=datetime.date(2023, 1, 23))

    # Then the last sleep data is updated in the database
    actual_last_sleep_data = user_last_sleep_data(user.fitbit)
    assert actual_last_sleep_data == expected_new_last_sleep_data
