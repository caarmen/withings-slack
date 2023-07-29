import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.database import crud
from slackhealthbot.database.models import User
from slackhealthbot.services.fitbit import api
from slackhealthbot.services.models import ActivityData, SleepData
from slackhealthbot.settings import settings


async def save_new_sleep_data(
    db: AsyncSession,
    user: User,
    sleep_data: SleepData,
):
    await crud.update_user(
        db,
        user,
        fitbit_data={
            "last_sleep_start_time": sleep_data.start_time,
            "last_sleep_end_time": sleep_data.end_time,
            "last_sleep_sleep_minutes": sleep_data.sleep_minutes,
            "last_sleep_wake_minutes": sleep_data.wake_minutes,
        },
    )


async def save_new_activity_data(
    db: AsyncSession,
    user: User,
    activity_data: ActivityData,
):
    await crud.update_user(
        db,
        user,
        fitbit_data={
            "last_activity_log_id": activity_data.log_id,
        },
    )


def _is_new_valid_activity(user: User, activity: ActivityData | None):
    return (
        activity
        and activity.log_id != user.fitbit.last_activity_log_id
        and activity.type_id in settings.fitbit_activity_type_ids
    )


async def get_activity(
    db: AsyncSession,
    user: User,
    when: datetime.datetime,
):
    activity = await api.get_activity(db, user, when)
    if not _is_new_valid_activity(user, activity):
        return None
    await save_new_activity_data(db, user, activity)
    return activity
