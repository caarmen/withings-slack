from sqlalchemy.orm import Session

from slackhealthbot.database import crud
from slackhealthbot.database.models import User
from slackhealthbot.services.models import SleepData


def save_new_sleep_data(
    db: Session,
    user: User,
    sleep_data: SleepData,
):
    crud.update_user(
        db,
        user,
        fitbit_data={
            "last_sleep_start_time": sleep_data.start_time,
            "last_sleep_end_time": sleep_data.end_time,
            "last_sleep_sleep_minutes": sleep_data.sleep_minutes,
            "last_sleep_wake_minutes": sleep_data.wake_minutes,
        },
    )
