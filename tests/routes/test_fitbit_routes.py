import datetime
import json
import re

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from respx import MockRouter
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.database import crud
from slackhealthbot.database.models import FitbitLatestActivity, FitbitUser, User
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
async def test_sleep_notification(
    mocked_async_session,
    client: TestClient,
    respx_mock: MockRouter,
    user_factory: UserFactory,
    fitbit_user_factory: FitbitUserFactory,
    scenario: FitbitSleepScenario,
):
    """
    Given a user with a given previous sleep logged
    When we receive the callback from fitbit that a new sleep is available
    Then the last sleep is updated in the database
    And the message is posted to slack with the correct icons.
    """

    # Given a user with the given previous sleep data
    user: User = user_factory(fitbit=None)
    fitbit_user: FitbitUser = fitbit_user_factory(
        user_id=user.id,
        **scenario.input_initial_sleep_data,
        oauth_expiration_date=datetime.datetime.utcnow() + datetime.timedelta(days=1),
    )

    db_user = await crud.get_user(
        mocked_async_session, fitbit_oauth_userid=fitbit_user.oauth_userid
    )

    # Mock fitbit endpoint to return some sleep data
    respx_mock.get(
        url=f"{settings.fitbit_base_url}1.2/user/-/sleep/date/2023-05-12.json",
    ).mock(Response(status_code=200, json=scenario.input_mock_fitbit_response))

    # Mock an empty ok response from the slack webhook
    slack_request = respx_mock.post(f"{settings.slack_webhook_url}").mock(
        return_value=Response(200)
    )

    # When we receive the callback from fitbit that a new sleep is available
    response = client.post(
        "/fitbit-notification-webhook/",
        content=json.dumps(
            [
                {
                    "ownerId": user.fitbit.oauth_userid,
                    "date": 1683894606,
                    "collectionType": "sleep",
                }
            ]
        ),
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Then the last sleep data is updated in the database
    actual_last_sleep_data = user_last_sleep_data(db_user.fitbit)
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
async def test_activity_notification(
    mocked_async_session: AsyncSession,
    client: TestClient,
    respx_mock: MockRouter,
    user_factory: UserFactory,
    fitbit_user_factory: FitbitUserFactory,
    fitbit_latest_activity_factory: FitbitLatestActivityFactory,
    scenario: FitbitActivityScenario,
):
    """
    Given a user with a given previous activity logged
    When we receive the callback from fitbit that a new activity is available
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

    # Mock fitbit endpoint to return some activity data
    respx_mock.get(
        url=f"{settings.fitbit_base_url}1/user/-/activities/list.json",
    ).mock(Response(status_code=200, json=scenario.input_mock_fitbit_response))

    # Mock an empty ok response from the slack webhook
    slack_request = respx_mock.post(f"{settings.slack_webhook_url}").mock(
        return_value=Response(200)
    )

    # When we receive the callback from fitbit that a new activity is available
    response = client.post(
        "/fitbit-notification-webhook/",
        content=json.dumps(
            [
                {
                    "ownerId": user.fitbit.oauth_userid,
                    "date": 1683894606,
                    "collectionType": "activities",
                }
            ]
        ),
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Then the latest activity data is updated in the database
    db_user = await crud.get_user(
        db=mocked_async_session, fitbit_oauth_userid=fitbit_user.oauth_userid
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
        assert "None" not in actual_message
    else:
        assert not slack_request.calls


@pytest.mark.asyncio
async def test_retry_authentication(
    mocked_async_session,
    client: TestClient,
    respx_mock: MockRouter,
    user_factory: UserFactory,
    fitbit_user_factory: FitbitUserFactory,
):
    """
    Given a user whose access token is no longer valid
    When we receive the callback from fitbit that a new activity is available
    Then the access token is refreshed
    And the latest activity is updated in the database
    And the message is posted to slack with the correct pattern.
    """

    scenario = activity_scenarios["No previous activity data, new Spinning activity"]

    # Given a user
    user: User = user_factory(fitbit=None)
    fitbit_user: FitbitUser = fitbit_user_factory(
        user_id=user.id,
        oauth_expiration_date=datetime.datetime.utcnow() + datetime.timedelta(days=1),
    )

    # Given the user's access token is no longer valid:

    fitbit_activity_request = respx_mock.get(
        url=f"{settings.fitbit_base_url}1/user/-/activities/list.json",
    ).mock(
        side_effect=[
            # Mock fitbit endpoint to return an unauthorized error
            Response(status_code=401),
            # Mock fitbit endpoint to return some activity data
            Response(status_code=200, json=scenario.input_mock_fitbit_response),
        ]
    )

    # Mock fitbit oauth refresh token success
    oauth_token_refresh_request = respx_mock.post(
        url=f"{settings.fitbit_base_url}oauth2/token",
    ).mock(
        Response(
            status_code=200,
            json={
                "user_id": user.fitbit.oauth_userid,
                "access_token": "some new access token",
                "refresh_token": "some new refresh token",
                "expires_in": 600,
            },
        )
    )

    # Mock an empty ok response from the slack webhook
    slack_request = respx_mock.post(f"{settings.slack_webhook_url}").mock(
        return_value=Response(200)
    )

    # When we receive the callback from fitbit that a new activity is available
    response = client.post(
        "/fitbit-notification-webhook/",
        content=json.dumps(
            [
                {
                    "ownerId": user.fitbit.oauth_userid,
                    "date": 1683894606,
                    "collectionType": "activities",
                }
            ]
        ),
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    db_user = await crud.get_user(
        db=mocked_async_session, fitbit_oauth_userid=fitbit_user.oauth_userid
    )

    # Then the access token is refreshed.
    assert fitbit_activity_request.call_count == 2
    assert oauth_token_refresh_request.call_count == 1
    assert db_user.fitbit.oauth_access_token == "some new access token"
    assert db_user.fitbit.oauth_refresh_token == "some new refresh token"

    # And the latest activity data is updated in the database
    latest_activities: list[
        FitbitLatestActivity
    ] = await db_user.fitbit.awaitable_attrs.latest_activities
    assert latest_activities[0].log_id == scenario.expected_new_last_activity_log_id

    # And the message was sent to slack as expected
    actual_message = json.loads(slack_request.calls[0].request.content)["text"].replace(
        "\n", ""
    )
    assert re.search(scenario.expected_message_pattern, actual_message)
    assert "None" not in actual_message
