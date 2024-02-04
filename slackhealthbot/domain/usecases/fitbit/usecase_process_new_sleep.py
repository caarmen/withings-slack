import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.domain.modelmappers.domaintorepository.sleep import (
    core_sleep_to_repository_sleep,
)
from slackhealthbot.domain.models.sleep import SleepData
from slackhealthbot.domain.usecases.fitbit import usecase_get_last_sleep
from slackhealthbot.domain.usecases.slack import usecase_post_sleep
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
        sleep=core_sleep_to_repository_sleep(new_sleep_data),
    )
    await usecase_post_sleep.do(
        slack_alias=user_identity.slack_alias,
        new_sleep_data=new_sleep_data,
        last_sleep_data=core_sleep_to_repository_sleep(last_sleep_data),
    )
    return new_sleep_data
