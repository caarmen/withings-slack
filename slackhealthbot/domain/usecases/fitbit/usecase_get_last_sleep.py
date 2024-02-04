import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.data.repositories import fitbitrepository
from slackhealthbot.domain.modelmappers.remoteservicetodomain.sleep import (
    remote_service_sleep_to_domain_sleep,
)
from slackhealthbot.domain.models.sleep import SleepData
from slackhealthbot.remoteservices.fitbit import sleepapi


async def do(
    db: AsyncSession,
    fitbit_userid: str,
    when: datetime.date,
) -> SleepData | None:
    user: fitbitrepository.User = await fitbitrepository.get_user_by_fitbit_userid(
        db,
        fitbit_userid=fitbit_userid,
    )
    last_sleep: sleepapi.FitbitSleep = await sleepapi.get_sleep(
        oauth_token=user.oauth_data,
        when=when,
    )
    return remote_service_sleep_to_domain_sleep(last_sleep)
