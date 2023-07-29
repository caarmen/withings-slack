import datetime
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.database import models as db_models
from slackhealthbot.services import models as svc_models
from slackhealthbot.services.fitbit import parser, requests
from slackhealthbot.settings import settings


async def subscribe(db: AsyncSession, user: db_models.User):
    for collectionPath in ["sleep", "activities"]:
        response = await requests.post(
            db,
            user=user,
            url=f"{settings.fitbit_base_url}1/user/-/{collectionPath}/apiSubscriptions/{user.fitbit.oauth_userid}-{collectionPath}.json",
        )
        logging.info(
            f"Fitbit {collectionPath} subscription response: {response.json()}"
        )


async def get_sleep(
    db: AsyncSession,
    user: db_models.User,
    when: datetime.date,
) -> Optional[svc_models.SleepData]:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    logging.info(f"get_sleep for user {user.fitbit.oauth_userid}")
    when_str = when.strftime("%Y-%m-%d")
    response = await requests.get(
        db,
        user=user,
        url=f"{settings.fitbit_base_url}1.2/user/-/sleep/date/{when_str}.json",
    )
    return parser.parse_sleep(response.content, slack_alias=user.slack_alias)


async def get_activity(
    db: AsyncSession, user: db_models.User, when: datetime.datetime
) -> Optional[svc_models.ActivityData]:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    logging.info(f"get_activity for user {user.fitbit.oauth_userid}")
    when_str = when.strftime("%Y-%m-%dT%H:%M:%S")
    response = await requests.get(
        db,
        user=user,
        url=f"{settings.fitbit_base_url}1/user/-/activities/list.json",
        params={
            "beforeDate": when_str,
            "sort": "desc",
            "offset": 0,
            "limit": 1,
        },
    )
    return parser.parse_activity(response.content)
