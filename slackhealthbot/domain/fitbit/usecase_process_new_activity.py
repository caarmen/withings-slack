import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import (
    ActivityData,
    ActivityHistory,
    ActivityZone,
    ActivityZoneMinutes,
)
from slackhealthbot.domain.fitbit import usecase_get_last_activity
from slackhealthbot.domain.slack import usecase_post_activity
from slackhealthbot.repositories import fitbitrepository
from slackhealthbot.settings import settings


async def do(
    db: AsyncSession,
    fitbit_userid: str,
    when: datetime.date,
) -> ActivityData:
    user_identity: fitbitrepository.UserIdentity = (
        await fitbitrepository.get_user_identity_by_fitbit_userid(
            db,
            fitbit_userid=fitbit_userid,
        )
    )
    new_activity_data: ActivityData = await usecase_get_last_activity.do(
        db=db,
        fitbit_userid=fitbit_userid,
        when=when,
    )
    if not new_activity_data:
        return None

    if not await _is_new_valid_activity(
        db,
        fitbit_userid=fitbit_userid,
        type_id=new_activity_data.type_id,
        log_id=new_activity_data.log_id,
    ):
        return None

    last_activity_data: fitbitrepository.Activity = (
        await fitbitrepository.get_latest_activity_by_user_and_type(
            db=db,
            fitbit_userid=fitbit_userid,
            type_id=new_activity_data.type_id,
        )
    )
    await fitbitrepository.create_activity_for_user(
        db=db,
        fitbit_userid=fitbit_userid,
        activity=fitbitrepository.Activity(
            log_id=new_activity_data.log_id,
            total_minutes=new_activity_data.total_minutes,
            calories=new_activity_data.calories,
            type_id=new_activity_data.type_id,
            **{f"{x.zone}_minutes": x.minutes for x in new_activity_data.zone_minutes},
        ),
    )
    await usecase_post_activity.do(
        slack_alias=user_identity.slack_alias,
        activity_history=ActivityHistory(
            latest_activity_data=ActivityData(
                log_id=last_activity_data.log_id,
                type_id=last_activity_data.type_id,
                name=new_activity_data.name,
                calories=last_activity_data.calories,
                total_minutes=last_activity_data.total_minutes,
                zone_minutes=[
                    ActivityZoneMinutes(
                        zone=x,
                        minutes=getattr(last_activity_data, f"{x}_minutes"),
                    )
                    for x in ActivityZone
                    if getattr(last_activity_data, f"{x}_minutes")
                ],
            )
            if last_activity_data
            else None,
            new_activity_data=new_activity_data,
        ),
    )

    return new_activity_data


async def _is_new_valid_activity(
    db: AsyncSession,
    fitbit_userid: str,
    type_id: int,
    log_id: str,
) -> bool:
    return (
        type_id in settings.fitbit_activity_type_ids
        and not await fitbitrepository.get_activity_by_user_and_log_id(
            db=db,
            fitbit_userid=fitbit_userid,
            log_id=log_id,
        )
    )
