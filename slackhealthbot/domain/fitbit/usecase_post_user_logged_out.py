from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.domain.slack import (
    usecase_post_user_logged_out as slack_usecase_post_user_logged_out,
)
from slackhealthbot.repositories import fitbitrepository


async def do(
    db: AsyncSession,
    fitbit_userid: str,
):
    user_identity: fitbitrepository.UserIdentity = (
        await fitbitrepository.get_user_identity_by_fitbit_userid(
            db,
            fitbit_userid=fitbit_userid,
        )
    )
    await slack_usecase_post_user_logged_out.do(
        slack_alias=user_identity.slack_alias,
        service="fitbit",
    )
