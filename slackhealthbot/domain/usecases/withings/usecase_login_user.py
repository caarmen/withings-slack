from typing import Any

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.modelmappers.remoteservicetocore import oauth
from slackhealthbot.domain.repository.withingsrepository import (
    User,
    UserIdentity,
    WithingsRepository,
)
from slackhealthbot.remoteservices.withings import subscribeapi


async def do(
    repo: WithingsRepository,
    slack_alias: str,
    token: dict[str, Any],
):
    user: User = await _upsert_user(repo, slack_alias, token)
    await subscribeapi.subscribe(oauth_token=user.oauth_data)


async def _upsert_user(
    repo: WithingsRepository, slack_alias: str, token: dict[str, Any]
) -> User:
    oauth_fields: OAuthFields = oauth.remote_service_oauth_to_core_oauth(token)
    user_identity: UserIdentity = await repo.get_user_identity_by_withings_userid(
        withings_userid=oauth_fields.oauth_userid
    )
    if not user_identity:
        return await repo.create_user(
            slack_alias=slack_alias,
            withings_userid=oauth_fields.oauth_userid,
            oauth_data=oauth_fields,
        )
    else:
        await repo.update_oauth_data(
            withings_userid=oauth_fields.oauth_userid,
            oauth_data=oauth_fields,
        )
    return await repo.get_user_by_withings_userid(
        withings_userid=oauth_fields.oauth_userid,
    )
