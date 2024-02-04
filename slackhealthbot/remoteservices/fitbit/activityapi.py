import datetime
import json
import logging
from typing import Self

from pydantic import BaseModel

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.oauth import requests
from slackhealthbot.settings import fitbit_oauth_settings as settings


class FitbitMinutesInHeartRateZone(BaseModel):
    minutes: int
    type: str


class FitBitActiveZoneMinutes(BaseModel):
    minutesInHeartRateZones: list[FitbitMinutesInHeartRateZone]


class FitbitActivity(BaseModel):
    logId: int
    activeZoneMinutes: FitBitActiveZoneMinutes = FitBitActiveZoneMinutes(
        minutesInHeartRateZones=[]
    )
    activityName: str
    activityTypeId: int
    calories: int
    duration: int


class FitbitActivities(BaseModel):
    activities: list[FitbitActivity]

    @classmethod
    def parse(cls, input: str) -> Self:
        return cls(**json.loads(input))


async def get_activity(
    oauth_token: OAuthFields, when: datetime.datetime
) -> FitbitActivities | None:
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
    try:
        return FitbitActivities.parse(response.content)
    except Exception as e:
        logging.warning(
            f"Error parsing activity: error {e}, input: {input}", exc_info=e
        )
        return None
