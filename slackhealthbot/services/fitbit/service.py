import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.database import crud
from slackhealthbot.database.models import FitbitActivity, User
from slackhealthbot.services.fitbit import api
from slackhealthbot.services.models import (
    ActivityData,
    ActivityHistory,
    ActivityZone,
    ActivityZoneMinutes,
    SleepData,
)
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
    await crud.upsert_fitbit_activity_data(
        db,
        fitbit_user_id=user.fitbit.id,
        type_id=activity_data.type_id,
        data={
            **activity_data.model_dump(include={"log_id", "total_minutes", "calories"}),
            **{f"{x.zone}_minutes": x.minutes for x in activity_data.zone_minutes},
        },
    )
    await db.refresh(user)


async def _is_new_valid_activity(
    db: AsyncSession, user: User, activity: ActivityData | None
) -> bool:
    return (
        activity
        and activity.type_id in settings.fitbit_activity_type_ids
        and not await crud.get_activity_by_user_and_log_id(
            db=db, fitbit_user_id=user.fitbit.id, log_id=activity.log_id
        )
    )


async def get_latest_activity(
    db: AsyncSession,
    user: User,
    type_id: int,
    name: str,
) -> ActivityData | None:
    latest_activity: FitbitActivity = await crud.get_latest_activity_by_user_and_type(
        db=db,
        fitbit_user_id=user.fitbit.id,
        type_id=type_id,
    )
    if not latest_activity:
        return None
    return (
        ActivityData(
            log_id=latest_activity.log_id,
            type_id=latest_activity.type_id,
            name=name,
            calories=latest_activity.calories,
            total_minutes=latest_activity.total_minutes,
            zone_minutes=[
                ActivityZoneMinutes(
                    zone=x,
                    minutes=getattr(latest_activity, f"{x}_minutes"),
                )
                for x in ActivityZone
                if getattr(latest_activity, f"{x}_minutes")
            ],
        )
        if latest_activity
        else None
    )


async def get_activity(
    db: AsyncSession,
    user: User,
    when: datetime.datetime,
) -> ActivityHistory | None:
    activity = await api.get_activity(user, when)
    if not await _is_new_valid_activity(db, user, activity):
        return None
    latest_activity = await get_latest_activity(
        db=db, user=user, type_id=activity.type_id, name=activity.name
    )
    await save_new_activity_data(db, user, activity)
    return ActivityHistory(
        latest_activity_data=latest_activity, new_activity_data=activity
    )
