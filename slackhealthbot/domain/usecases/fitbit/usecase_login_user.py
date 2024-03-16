from typing import Any

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.localrepository.localfitbitrepository import (
    LocalFitbitRepository,
    User,
    UserIdentity,
)
from slackhealthbot.domain.modelmappers.remoteservicetocore import oauth
from slackhealthbot.domain.remoterepository.remotefitbitrepository import (
    RemoteFitbitRepository,
)


async def do(
    local_repo: LocalFitbitRepository,
    remote_repo: RemoteFitbitRepository,
    slack_alias: str,
    token: dict[str, Any],
):
    user: User = await _upsert_user(local_repo, slack_alias, token)
    await remote_repo.subscribe(oauth_fields=user.oauth_data)


async def _upsert_user(
    repo: LocalFitbitRepository, slack_alias: str, token: dict[str, Any]
) -> User:
    oauth_fields: OAuthFields = oauth.remote_service_oauth_to_core_oauth(token)
    user_identity: UserIdentity = await repo.get_user_identity_by_fitbit_userid(
        fitbit_userid=oauth_fields.oauth_userid
    )
    if not user_identity:
        return await repo.create_user(
            slack_alias=slack_alias,
            fitbit_userid=oauth_fields.oauth_userid,
            oauth_data=oauth_fields,
        )
    else:
        await repo.update_oauth_data(
            fitbit_userid=oauth_fields.oauth_userid,
            oauth_data=oauth_fields,
        )
    return await repo.get_user_by_fitbit_userid(
        fitbit_userid=oauth_fields.oauth_userid,
    )
