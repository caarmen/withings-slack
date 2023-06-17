import dataclasses
import datetime
import logging
from threading import Timer
from typing import Optional

from sqlalchemy.orm import Session

from slackhealthbot.database import models
from slackhealthbot.database.connection import SessionLocal
from slackhealthbot.services import slack
from slackhealthbot.services.exceptions import UserLoggedOutException
from slackhealthbot.services.fitbit import api as fitbit_api
from slackhealthbot.services.fitbit.service import save_new_sleep_data
from slackhealthbot.services.models import SleepData, user_last_sleep_data
from slackhealthbot.settings import settings


@dataclasses.dataclass
class Cache:
    cache_success: dict[str, datetime.date] = dataclasses.field(default_factory=dict)
    cache_fail: dict[str, datetime.date] = dataclasses.field(default_factory=dict)


def handle_success_poll(
    db: Session,
    fitbit_user: models.FitbitUser,
    sleep_data: Optional[SleepData],
    when: datetime.date,
    cache: Cache,
):
    if sleep_data:
        last_sleep_data = user_last_sleep_data(fitbit_user)
        save_new_sleep_data(db, fitbit_user.user, sleep_data)
        slack.post_sleep(
            slack_alias=fitbit_user.user.slack_alias,
            new_sleep_data=sleep_data,
            last_sleep_data=last_sleep_data,
        )
        cache.cache_success[fitbit_user.oauth_userid] = when
        cache.cache_fail.pop(fitbit_user.oauth_userid, None)


def handle_fail_poll(
    fitbit_user: models.FitbitUser,
    when: datetime.date,
    cache: Cache,
):
    last_error_post = cache.cache_fail.get(fitbit_user.oauth_userid)
    if not last_error_post or last_error_post < when:
        slack.post_user_logged_out(
            slack_alias=fitbit_user.user.slack_alias,
            service="fitbit",
        )
        cache.cache_fail[fitbit_user.oauth_userid] = when


def fitbit_poll(cache: Cache):
    logging.info("fitbit poll")
    today = datetime.date.today()
    try:
        with SessionLocal() as db:
            do_poll(db, cache, when=today)
    except Exception:
        logging.error("Error polling fitbit", exc_info=True)
    schedule_fitbit_poll(cache=cache)


def do_poll(db: Session, cache: Cache, when: datetime.date):
    fitbit_users = db.query(models.FitbitUser).all()
    for fitbit_user in fitbit_users:
        latest_successful_poll = cache.cache_success.get(fitbit_user.oauth_userid)
        if not latest_successful_poll or latest_successful_poll < when:
            try:
                sleep_data = fitbit_api.get_sleep(
                    db,
                    user=fitbit_user.user,
                    when=when,
                )
            except UserLoggedOutException:
                handle_fail_poll(
                    fitbit_user=fitbit_user,
                    when=when,
                    cache=cache,
                )
            else:
                handle_success_poll(
                    db=db,
                    fitbit_user=fitbit_user,
                    sleep_data=sleep_data,
                    when=when,
                    cache=cache,
                )


def schedule_fitbit_poll(
    delay_s: int = settings.fitbit_poll_interval_s, cache: Cache = None
):
    if cache is None:
        cache = Cache()
    timer = Timer(delay_s, function=fitbit_poll, args=[cache])
    timer.daemon = True
    timer.start()
