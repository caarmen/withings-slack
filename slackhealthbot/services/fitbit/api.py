import datetime
import logging
from typing import Optional

from sqlalchemy.orm import Session

from slackhealthbot.database import models as db_models
from slackhealthbot.services import models as svc_models
from slackhealthbot.services.fitbit import parser, requests
from slackhealthbot.settings import settings


async def subscribe(db: Session, user: db_models.User):
    response = await requests.post(
        db,
        user=user,
        url=f"{settings.fitbit_base_url}1/user/-/sleep/apiSubscriptions/{user.fitbit.oauth_userid}.json",
    )
    logging.info(f"Fitbit subscription response: {response.json()}")


async def get_sleep(
    db: Session,
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
