import datetime

from slackhealthbot.domain.localrepository.localfitbitrepository import (
    LocalFitbitRepository,
    User,
)
from slackhealthbot.domain.models.activity import ActivityData
from slackhealthbot.domain.remoterepository.remotefitbitrepository import (
    RemoteFitbitRepository,
)


async def do(
    local_repo: LocalFitbitRepository,
    remote_repo: RemoteFitbitRepository,
    fitbit_userid: str,
    when: datetime.datetime,
) -> tuple[str, ActivityData] | None:
    user: User = await local_repo.get_user_by_fitbit_userid(
        fitbit_userid=fitbit_userid,
    )
    return await remote_repo.get_activity(
        oauth_fields=user.oauth_data,
        when=when,
    )
