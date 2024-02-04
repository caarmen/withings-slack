import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import SleepData
from slackhealthbot.domain.fitbit import usecase_get_last_sleep
from slackhealthbot.domain.slack import usecase_post_sleep
from slackhealthbot.repositories import fitbitrepository


async def do(
    db: AsyncSession,
    fitbit_userid: str,
    when: datetime.date,
) -> SleepData:
    user_identity: fitbitrepository.UserIdentity = (
        await fitbitrepository.get_user_identity_by_fitbit_userid(
            db,
            fitbit_userid=fitbit_userid,
        )
    )
    last_sleep_data: fitbitrepository.Sleep = (
        await fitbitrepository.get_sleep_by_fitbit_userid(
            db,
            fitbit_userid=fitbit_userid,
        )
    )
    new_sleep_data: SleepData = await usecase_get_last_sleep.do(
        db=db,
        fitbit_userid=fitbit_userid,
        when=when,
    )
    if not new_sleep_data:
        return None
    await fitbitrepository.update_sleep_for_user(
        db=db,
        fitbit_userid=fitbit_userid,
        sleep=fitbitrepository.Sleep(
            start_time=new_sleep_data.start_time,
            end_time=new_sleep_data.end_time,
            sleep_minutes=new_sleep_data.sleep_minutes,
            wake_minutes=new_sleep_data.wake_minutes,
        ),
    )
    await usecase_post_sleep.do(
        slack_alias=user_identity.slack_alias,
        new_sleep_data=new_sleep_data,
        last_sleep_data=None
        if not last_sleep_data
        else SleepData(
            start_time=last_sleep_data.start_time,
            end_time=last_sleep_data.end_time,
            sleep_minutes=last_sleep_data.sleep_minutes,
            wake_minutes=last_sleep_data.wake_minutes,
        ),
    )
    return new_sleep_data
