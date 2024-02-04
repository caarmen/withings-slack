import datetime
import logging
from typing import Optional

from slackhealthbot.core.models import ActivityData, OAuthFields, SleepData
from slackhealthbot.oauth import requests
from slackhealthbot.remoteservices.fitbit import parser
from slackhealthbot.settings import fitbit_oauth_settings as settings


async def subscribe(
    fitbit_userid: str,
    oauth_token: OAuthFields,
):
    for collectionPath in ["sleep", "activities"]:
        response = await requests.post(
            provider=settings.name,
            token=oauth_token,
            url=f"{settings.base_url}1/user/-/{collectionPath}/apiSubscriptions/{fitbit_userid}-{collectionPath}.json",
        )
        logging.info(
            f"Fitbit {collectionPath} subscription response: {response.json()}"
        )


async def get_sleep(
    oauth_token: OAuthFields,
    when: datetime.date,
) -> Optional[SleepData]:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    logging.info("get_sleep for user")
    when_str = when.strftime("%Y-%m-%d")
    response = await requests.get(
        provider=settings.name,
        token=oauth_token,
        url=f"{settings.base_url}1.2/user/-/sleep/date/{when_str}.json",
    )
    return parser.parse_sleep(response.content)


async def get_activity(
    oauth_token: OAuthFields, when: datetime.datetime
) -> Optional[ActivityData]:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    logging.info("get_activity for user")
    when_str = when.strftime("%Y-%m-%dT%H:%M:%S")
    response = await requests.get(
        provider=settings.name,
        token=oauth_token,
        url=f"{settings.base_url}1/user/-/activities/list.json",
        params={
            "beforeDate": when_str,
            "sort": "desc",
            "offset": 0,
            "limit": 1,
        },
    )
    return parser.parse_activity(response.content)
