import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import SleepData
from slackhealthbot.repositories import fitbitrepository
from slackhealthbot.services.fitbit import api


async def do(
    db: AsyncSession,
    fitbit_userid: str,
    when: datetime.date,
) -> SleepData | None:
    user: fitbitrepository.User = await fitbitrepository.get_user_by_fitbit_userid(
        db,
        fitbit_userid=fitbit_userid,
    )
    last_sleep: SleepData = await api.get_sleep(
        oauth_token=user.oauth_data,
        when=when,
    )
    return last_sleep
