from slackhealthbot.domain.localrepository.localwithingsrepository import (
    LocalWithingsRepository,
    UserIdentity,
)
from slackhealthbot.domain.remoterepository.remoteslackrepository import (
    RemoteSlackRepository,
)
from slackhealthbot.domain.usecases.slack import (
    usecase_post_user_logged_out as slack_usecase_post_user_logged_out,
)


async def do(
    withings_repo: LocalWithingsRepository,
    slack_repo: RemoteSlackRepository,
    withings_userid: str,
):
    user_identity: UserIdentity = (
        await withings_repo.get_user_identity_by_withings_userid(
            withings_userid=withings_userid,
        )
    )
    await slack_usecase_post_user_logged_out.do(
        repo=slack_repo,
        slack_alias=user_identity.slack_alias,
        service="withings",
    )
