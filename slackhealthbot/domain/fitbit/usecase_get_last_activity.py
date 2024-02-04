import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import ActivityData
from slackhealthbot.repositories import fitbitrepository
from slackhealthbot.services.fitbit import api


async def do(
    db: AsyncSession,
    fitbit_userid: str,
    when: datetime.date,
) -> ActivityData | None:
    user: fitbitrepository.User = await fitbitrepository.get_user_by_fitbit_userid(
        db,
        fitbit_userid=fitbit_userid,
    )
    last_activity: ActivityData = await api.get_activity(
        oauth_token=user.oauth_data,
        when=when,
    )
    return last_activity
