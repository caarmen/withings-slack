import datetime
import json
import re

import pytest
from httpx import Response
from respx import MockRouter

from slackhealthbot.database import crud
from slackhealthbot.database.models import FitbitLatestActivity, FitbitUser, User
from slackhealthbot.scheduler import Cache, do_poll
from slackhealthbot.services.models import user_last_sleep_data
from slackhealthbot.settings import settings
from tests.factories.factories import (
    FitbitLatestActivityFactory,
    FitbitUserFactory,
    UserFactory,
)
from tests.fixtures.fitbit_scenarios import (
    FitbitActivityScenario,
    FitbitSleepScenario,
    activity_scenarios,
    sleep_scenarios,
)


@pytest.mark.parametrize(
    ids=sleep_scenarios.keys(),
    argnames="scenario",
    argvalues=sleep_scenarios.values(),
)
@pytest.mark.asyncio
async def test_fitbit_poll_sleep(
    mocked_async_session,
    respx_mock: MockRouter,
    user_factory: UserFactory,
    fitbit_user_factory: FitbitUserFactory,
    scenario: FitbitSleepScenario,
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
        **scenario.input_initial_sleep_data,
        oauth_expiration_date=datetime.datetime.utcnow() + datetime.timedelta(days=1),
    )

    # Mock fitbit endpoint to return no activity data
    respx_mock.get(
        url=f"{settings.fitbit_base_url}1/user/-/activities/list.json",
    ).mock(Response(status_code=200, json={"activities": []}))

    # Mock fitbit endpoint to return some sleep data
    respx_mock.get(
        url=f"{settings.fitbit_base_url}1.2/user/-/sleep/date/2023-01-23.json",
    ).mock(Response(status_code=200, json=scenario.input_mock_fitbit_response))

    # Mock an empty ok response from the slack webhook
    slack_request = respx_mock.post(f"{settings.slack_webhook_url}").mock(
        return_value=Response(200)
    )

    # When we poll for new sleep data
    await do_poll(
        db=mocked_async_session, cache=Cache(), when=datetime.date(2023, 1, 23)
    )

    # Then the last sleep data is updated in the database
    actual_last_sleep_data = user_last_sleep_data(user.fitbit)
    assert actual_last_sleep_data == scenario.expected_new_last_sleep_data

    # And the message was sent to slack as expected
    if scenario.expected_icons is not None:
        actual_message = json.loads(slack_request.calls[0].request.content)[
            "text"
        ].replace("\n", "")
        assert re.search(scenario.expected_icons, actual_message)
    else:
        assert not slack_request.calls


@pytest.mark.parametrize(
    ids=activity_scenarios.keys(),
    argnames="scenario",
    argvalues=activity_scenarios.values(),
)
@pytest.mark.asyncio
async def test_fitbit_poll_activity(
    mocked_async_session,
    respx_mock: MockRouter,
    user_factory: UserFactory,
    fitbit_user_factory: FitbitUserFactory,
    fitbit_latest_activity_factory: FitbitLatestActivityFactory,
    scenario: FitbitActivityScenario,
):
    """
    Given a user with given previous activity data logged
    When we poll fitbit to get new activity data
    Then the latest activity is updated in the database
    And the message is posted to slack with the correct pattern.
    """

    # Given a user with the given previous activity data
    user: User = user_factory(fitbit=None)
    fitbit_user: FitbitUser = fitbit_user_factory(
        user_id=user.id,
        oauth_expiration_date=datetime.datetime.utcnow() + datetime.timedelta(days=1),
    )
    if scenario.input_initial_activity_data:
        fitbit_latest_activity_factory(
            fitbit_user_id=fitbit_user.id,
            type_id=55001,
            **scenario.input_initial_activity_data,
        )

    # Mock fitbit endpoint to return no sleep data
    respx_mock.get(
        url=f"{settings.fitbit_base_url}1.2/user/-/sleep/date/2023-01-23.json",
    ).mock(Response(status_code=200, json={"sleep": []}))

    # Mock fitbit endpoint to return some activity data
    respx_mock.get(
        url=f"{settings.fitbit_base_url}1/user/-/activities/list.json",
    ).mock(Response(status_code=200, json=scenario.input_mock_fitbit_response))

    # Mock an empty ok response from the slack webhook
    slack_request = respx_mock.post(f"{settings.slack_webhook_url}").mock(
        return_value=Response(200)
    )

    # When we poll for new sleep data
    await do_poll(
        db=mocked_async_session, cache=Cache(), when=datetime.date(2023, 1, 23)
    )

    # Then the latest activity data is updated in the database
    db_user = await crud.get_user(
        db=mocked_async_session, fitbit_oauth_userid=user.fitbit.oauth_userid
    )
    latest_activities: list[
        FitbitLatestActivity
    ] = await db_user.fitbit.awaitable_attrs.latest_activities
    if scenario.is_new_log_expected:
        assert latest_activities[0].log_id == scenario.expected_new_last_activity_log_id
    elif scenario.input_initial_activity_data:
        assert (
            latest_activities[0].log_id
            == scenario.input_initial_activity_data["log_id"]
        )
    else:
        assert not latest_activities

    # And the message was sent to slack as expected
    if scenario.expected_message_pattern:
        actual_message = json.loads(slack_request.calls[0].request.content)[
            "text"
        ].replace("\n", "")
        assert re.search(scenario.expected_message_pattern, actual_message)
    else:
        assert not slack_request.calls
