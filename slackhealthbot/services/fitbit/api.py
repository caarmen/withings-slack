import datetime
import logging
from typing import Optional

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from slackhealthbot.database import crud
from slackhealthbot.database import models as db_models
from slackhealthbot.services import models as svc_models
from slackhealthbot.services.fitbit import parser, requests
from slackhealthbot.settings import settings


def subscribe(db: Session, user: db_models.User):
    response = requests.post(
        db,
        user=user,
        url=f"{settings.fitbit_base_url}1/user/-/sleep/apiSubscriptions/{user.fitbit.oauth_userid}.json",
    )
    logging.info(f"Fitbit subscription response: {response.json()}")


def get_sleep(
    db: Session,
    userid: str,
    when: datetime.date,
) -> Optional[svc_models.WeightData]:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    logging.info(f"get_sleep for user {userid}")
    try:
        user = crud.get_user(db, fitbit_oauth_userid=userid)
    except NoResultFound:
        logging.info(f"get_sleep: User {userid} unknown")
        return None
    when_str = when.strftime("%Y-%m-%d")
    response = requests.get(
        db,
        user=user,
        url=f"{settings.fitbit_base_url}1.2/user/-/sleep/date/{when_str}.json",
    )
    return parser.parse_sleep(response.content, slack_alias=user.slack_alias)
