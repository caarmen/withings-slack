import datetime
import json
import re

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from respx import MockRouter

from slackhealthbot.database import crud
from slackhealthbot.database.models import FitbitUser, User
from slackhealthbot.services.models import user_last_sleep_data
from slackhealthbot.settings import settings
from tests.factories.factories import FitbitUserFactory, UserFactory
from tests.fixtures.fitbit_scenarios import FitbitSleepScenario, sleep_scenarios


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
    db_fitbit_user = db_user.fitbit
    # The user has the previous sleep logged
    assert (
        db_fitbit_user.last_sleep_sleep_minutes
        == scenario.input_initial_sleep_data["last_sleep_sleep_minutes"]
    )

    # Mock fitbit endpoint to return some sleep data
    respx_mock.get(
        url=f"{settings.fitbit_base_url}1.2/user/-/sleep/date/2023-05-12.json",
    ).mock(Response(status_code=200, json=scenario.input_mock_fitbit_response))

    # Mock an empty ok response from the slack webhook
    slack_request = respx_mock.post(f"{settings.slack_webhook_url}").mock(
        return_value=Response(200)
    )

    # When we receive the callback from fitbit that a new weight is available
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
    actual_message = json.loads(slack_request.calls[0].request.content)["text"].replace(
        "\n", ""
    )
    assert re.search(scenario.expected_icons, actual_message)
