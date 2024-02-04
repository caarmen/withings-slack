from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.modelmappers.coretorepository.oauthfitbit import (
    core_oauth_to_repository_oauth,
)
from slackhealthbot.domain.modelmappers.remoteservicetocore import oauth
from slackhealthbot.remoteservices.fitbit import subscribeapi
from slackhealthbot.repositories import fitbitrepository
from slackhealthbot.repositories.fitbitrepository import UserIdentity


async def do(
    db: AsyncSession,
    slack_alias: str,
    token: dict[str, Any],
):
    user: fitbitrepository.User = await _upsert_user(db, slack_alias, token)
    await subscribeapi.subscribe(
        fitbit_userid=user.identity.fitbit_userid, oauth_token=user.oauth_data
    )


async def _upsert_user(
    db: AsyncSession, slack_alias: str, token: dict[str, Any]
) -> fitbitrepository.User:
    oauth_fields: OAuthFields = oauth.remote_service_oauth_to_core_oauth(token)
    user_identity: UserIdentity = (
        await fitbitrepository.get_user_identity_by_fitbit_userid(
            db, fitbit_userid=oauth_fields.oauth_userid
        )
    )
    if not user_identity:
        return await fitbitrepository.create_user(
            db=db,
            slack_alias=slack_alias,
            fitbit_userid=oauth_fields.oauth_userid,
            oauth_data=core_oauth_to_repository_oauth(oauth_fields),
        )
    else:
        await fitbitrepository.update_oauth_data(
            db,
            fitbit_userid=oauth_fields.oauth_userid,
            oauth_data=core_oauth_to_repository_oauth(oauth_fields),
        )
    return await fitbitrepository.get_user_by_fitbit_userid(
        db,
        fitbit_userid=oauth_fields.oauth_userid,
    )
