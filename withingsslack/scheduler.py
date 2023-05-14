from threading import Timer
import datetime
from withingsslack.settings import settings
from withingsslack.services.fitbit import api as fitbit_api
from withingsslack.database.connection import SessionLocal
from withingsslack.database import models
from withingsslack.services import slack
import logging

_cache: dict[str, datetime.date] = {}


def fitbit_poll():
    logging.info("fitbit poll")
    with SessionLocal() as db:
        fitbit_users = db.query(models.FitbitUser).all()
        today = datetime.date.today()
        for fitbit_user in fitbit_users:
            latest_successful_poll = _cache.get(fitbit_user.oauth_userid)
            if not latest_successful_poll or latest_successful_poll < today:
                sleep_data = fitbit_api.get_sleep(
                    db,
                    userid=fitbit_user.oauth_userid,
                    when=today,
                )
                if sleep_data:
                    slack.post_sleep(sleep_data)
                    _cache[fitbit_user.oauth_userid] = today
    schedule_fitbit_poll()


def schedule_fitbit_poll(delay_s: int = settings.fitbit_poll_interval_s):
    timer = Timer(delay_s, fitbit_poll)
    timer.daemon = True
    timer.start()
