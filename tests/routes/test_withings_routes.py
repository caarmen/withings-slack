import datetime
import json
import math

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from respx import MockRouter

from slackhealthbot.database import crud
from slackhealthbot.database.models import User, WithingsUser
from slackhealthbot.settings import settings
from tests.factories.factories import UserFactory, WithingsUserFactory


@pytest.mark.parametrize(
    argnames="input_initial_weight, "
    "input_new_weight_g, "
    "expected_new_latest_weight_kg, "
    "expected_icon",
    argvalues=[
        (None, 52100, 52.1, ""),
        (52.1, 52200, 52.2, "↗️"),
        (52.1, 53200, 53.2, "⬆️"),
        (53.1, 53000, 53.0, "↘️"),
        (53.0, 51900, 51.9, "⬇️"),
        (52.3, 52300, 52.3, "➡️"),
    ],
)
@pytest.mark.asyncio
async def test_weight_notification(
    mocked_async_session,
    client: TestClient,
    respx_mock: MockRouter,
    user_factory: UserFactory,
    withings_user_factory: WithingsUserFactory,
    input_initial_weight,
    input_new_weight_g,
    expected_new_latest_weight_kg,
    expected_icon,
):
    """
    Given a user with a given previous weight logged
    When we receive the callback from withings that a new weight is available
    Then the last_weight is updated in the database
    And the message is posted to slack with the correct icon.
    """

    # Given a user
    user: User = user_factory(withings=None)
    withings_user: WithingsUser = withings_user_factory(
        user_id=user.id,
        last_weight=input_initial_weight,
        oauth_expiration_date=datetime.datetime.utcnow() + datetime.timedelta(days=1),
    )
    db_user = await crud.get_user(
        mocked_async_session, withings_oauth_userid=withings_user.oauth_userid
    )
    db_withings_user = db_user.withings
    # The user has the previous weight logged
    assert db_withings_user.last_weight == input_initial_weight

    # Mock withings endpoint to return some weight data
    respx_mock.post(
        url=f"{settings.withings_base_url}measure",
    ).mock(
        return_value=Response(
            status_code=200,
            json={
                "status": 0,
                "body": {
                    "measuregrps": [
                        {
                            "measures": [
                                {
                                    "value": input_new_weight_g,
                                    "unit": -3,
                                }
                            ],
                        },
                    ],
                },
            },
        )
    )

    # Mock an empty ok response from the slack webhook
    slack_request = respx_mock.post(url=f"{settings.slack_webhook_url}").mock(
        return_value=Response(status_code=200)
    )

    # When we receive the callback from withings that a new weight is available
    response = client.post(
        "/withings-notification-webhook/",
        data={
            "userid": withings_user.oauth_userid,
            "startdate": 1683894606,
            "enddate": 1686570821,
        },
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Then the last_weight is updated in the database
    assert math.isclose(db_user.withings.last_weight, expected_new_latest_weight_kg)

    # And the message is sent to slack as expected
    actual_message = json.loads(slack_request.calls[0].request.content)["text"]
    assert expected_icon in actual_message


@pytest.mark.asyncio
async def test_retry_authentication(
    mocked_async_session,
    client: TestClient,
    respx_mock: MockRouter,
    user_factory: UserFactory,
    withings_user_factory: WithingsUserFactory,
):
    """
    Given a user whose access token is no longer valid
    When we receive the callback from withings that a new weight is available
    Then the access token is refreshed
    And the latest weight is updated in the database
    And the message is posted to slack with the correct pattern.
    """
    # Given a user
    user: User = user_factory(withings=None)
    withings_user: WithingsUser = withings_user_factory(
        user_id=user.id,
        last_weight=50.2,
        oauth_expiration_date=datetime.datetime.utcnow() + datetime.timedelta(days=1),
    )

    # Given the user's access token is no longer valid:
    withings_weight_request = respx_mock.post(
        url=f"{settings.withings_base_url}measure",
    ).mock(
        side_effect=[
            # Mock withings endpoint to return an unauthorized error
            Response(
                status_code=200,
                json={
                    "status": 401,
                },
            ),
            # Mock withings endpoint to return some weight data
            Response(
                status_code=200,
                json={
                    "status": 0,
                    "body": {
                        "measuregrps": [
                            {
                                "measures": [
                                    {
                                        "value": 50050,
                                        "unit": -3,
                                    }
                                ],
                            },
                        ],
                    },
                },
            ),
        ]
    )

    # Mock withings oauth refresh token success
    respx_mock.post(
        url=f"{settings.withings_base_url}v2/signature/",
    ).mock(
        Response(
            status_code=200,
            json={
                "status": 0,
                "body": {
                    "nonce": "some nonce",
                },
            },
        )
    )
    oauth_token_refresh_request = respx_mock.post(
        url=f"{settings.withings_base_url}v2/oauth2",
    ).mock(
        Response(
            status_code=200,
            json={
                "status": 0,
                "body": {
                    "userid": user.withings.oauth_userid,
                    "access_token": "some new access token",
                    "refresh_token": "some new refresh token",
                    "expires_in": 600,
                },
            },
        )
    )

    # Mock an empty ok response from the slack webhook
    slack_request = respx_mock.post(url=f"{settings.slack_webhook_url}").mock(
        return_value=Response(status_code=200)
    )

    # When we receive the callback from withings that a new weight is available
    response = client.post(
        "/withings-notification-webhook/",
        data={
            "userid": withings_user.oauth_userid,
            "startdate": 1683894606,
            "enddate": 1686570821,
        },
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    db_user = await crud.get_user(
        db=mocked_async_session, withings_oauth_userid=withings_user.oauth_userid
    )
    # Then the access token is refreshed.
    assert withings_weight_request.call_count == 2
    assert oauth_token_refresh_request.call_count == 1
    assert db_user.withings.oauth_access_token == "some new access token"
    assert db_user.withings.oauth_refresh_token == "some new refresh token"

    # And the last_weight is updated in the database
    assert math.isclose(db_user.withings.last_weight, 50.05)

    # And the message is sent to slack as expected
    actual_message = json.loads(slack_request.calls[0].request.content)["text"]
    assert "↘️" in actual_message
