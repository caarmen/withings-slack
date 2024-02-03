import datetime
import logging
from typing import Optional

from slackhealthbot.core.models import ActivityData, SleepData
from slackhealthbot.database import models as db_models
from slackhealthbot.services.fitbit import parser
from slackhealthbot.services.fitbit.oauth import PROVIDER
from slackhealthbot.services.oauth import requests
from slackhealthbot.settings import settings


async def subscribe(user: db_models.User):
    for collectionPath in ["sleep", "activities"]:
        response = await requests.post(
            provider=PROVIDER,
            token=user.fitbit,
            url=f"{settings.fitbit_base_url}1/user/-/{collectionPath}/apiSubscriptions/{user.fitbit.oauth_userid}-{collectionPath}.json",
        )
        logging.info(
            f"Fitbit {collectionPath} subscription response: {response.json()}"
        )


async def get_sleep(
    user: db_models.User,
    when: datetime.date,
) -> Optional[SleepData]:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    logging.info(f"get_sleep for user {user.fitbit.oauth_userid}")
    when_str = when.strftime("%Y-%m-%d")
    response = await requests.get(
        provider=PROVIDER,
        token=user.fitbit,
        url=f"{settings.fitbit_base_url}1.2/user/-/sleep/date/{when_str}.json",
    )
    return parser.parse_sleep(response.content, slack_alias=user.slack_alias)


async def get_activity(
    user: db_models.User, when: datetime.datetime
) -> Optional[ActivityData]:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    logging.info(f"get_activity for user {user.fitbit.oauth_userid}")
    when_str = when.strftime("%Y-%m-%dT%H:%M:%S")
    response = await requests.get(
        provider=PROVIDER,
        token=user.fitbit,
        url=f"{settings.fitbit_base_url}1/user/-/activities/list.json",
        params={
            "beforeDate": when_str,
            "sort": "desc",
            "offset": 0,
            "limit": 1,
        },
    )
    return parser.parse_activity(response.content)
