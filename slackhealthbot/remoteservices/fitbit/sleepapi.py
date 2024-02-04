import datetime
import logging
from typing import Optional

from slackhealthbot.core.models import OAuthFields, SleepData
from slackhealthbot.oauth import requests
from slackhealthbot.remoteservices.fitbit import parser
from slackhealthbot.settings import fitbit_oauth_settings as settings


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
