from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.domain.slack import (
    usecase_post_user_logged_out as slack_usecase_post_user_logged_out,
)
from slackhealthbot.repositories import withingsrepository


async def do(
    db: AsyncSession,
    withings_userid: str,
):
    user_identity: withingsrepository.UserIdentity = (
        await withingsrepository.get_user_identity_by_withings_userid(
            db,
            withings_userid=withings_userid,
        )
    )
    await slack_usecase_post_user_logged_out.do(
        slack_alias=user_identity.slack_alias,
        service="withings",
    )
