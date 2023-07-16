import datetime
import json
import math

import pytest
from httpx import Response
from respx import MockRouter

from slackhealthbot.database import crud
from slackhealthbot.database.models import User, WithingsUser
from slackhealthbot.main import withings_notification_webhook
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
async def test_first_user_weight(
    mocked_async_session,
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
    # The user has no previous weight logged
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
    await withings_notification_webhook(
        userid=withings_user.oauth_userid,
        startdate=1683894606,
        enddate=1686570821,
        db=mocked_async_session,
    )

    # Then the last_weight is updated in the database
    assert math.isclose(db_user.withings.last_weight, expected_new_latest_weight_kg)

    # And the message is sent to slack as expected
    actual_message = json.loads(slack_request.calls[0].request.content)["text"]
    assert expected_icon in actual_message
