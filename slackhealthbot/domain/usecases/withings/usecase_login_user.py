from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.modelmappers.coretorepository.oauthwithings import (
    core_oauth_to_repository_oauth,
)
from slackhealthbot.domain.modelmappers.remoteservicetocore import oauth
from slackhealthbot.remoteservices.withings import subscribeapi
from slackhealthbot.repositories import withingsrepository
from slackhealthbot.repositories.withingsrepository import UserIdentity


async def do(
    db: AsyncSession,
    slack_alias: str,
    token: dict[str, Any],
):
    user: withingsrepository.User = await _upsert_user(db, slack_alias, token)
    await subscribeapi.subscribe(oauth_token=user.oauth_data)


async def _upsert_user(
    db: AsyncSession, slack_alias: str, token: dict[str, Any]
) -> withingsrepository.User:
    oauth_fields: OAuthFields = oauth.remote_service_oauth_to_core_oauth(token)
    user_identity: UserIdentity = (
        await withingsrepository.get_user_identity_by_withings_userid(
            db, withings_userid=oauth_fields.oauth_userid
        )
    )
    if not user_identity:
        return await withingsrepository.create_user(
            db=db,
            slack_alias=slack_alias,
            withings_userid=oauth_fields.oauth_userid,
            oauth_data=core_oauth_to_repository_oauth(oauth_fields),
        )
    else:
        await withingsrepository.update_oauth_data(
            db,
            withings_userid=oauth_fields.oauth_userid,
            oauth_data=core_oauth_to_repository_oauth(oauth_fields),
        )
    return await withingsrepository.get_user_by_withings_userid(
        db,
        withings_userid=oauth_fields.oauth_userid,
    )
