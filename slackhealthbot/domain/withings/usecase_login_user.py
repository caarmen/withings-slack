from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.oauth import usecase_parse_oauth
from slackhealthbot.repositories import withingsrepository
from slackhealthbot.repositories.withingsrepository import OAuthData, UserIdentity
from slackhealthbot.services.withings import api


async def do(
    db: AsyncSession,
    slack_alias: str,
    token: dict[str, Any],
):
    user: withingsrepository.User = await _upsert_user(db, slack_alias, token)
    await api.subscribe(oauth_token=user.oauth_data)


async def _upsert_user(
    db: AsyncSession, slack_alias: str, token: dict[str, Any]
) -> withingsrepository.User:
    oauth_fields: OAuthFields = usecase_parse_oauth.do(token)
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
            oauth_access_token=oauth_fields.oauth_access_token,
            oauth_refresh_token=oauth_fields.oauth_refresh_token,
            oauth_expiration_date=oauth_fields.oauth_expiration_date,
        )
    await withingsrepository.update_oauth_data(
        db,
        withings_userid=oauth_fields.oauth_userid,
        oauth_data=OAuthData(
            oauth_access_token=oauth_fields.oauth_access_token,
            oauth_refresh_token=oauth_fields.oauth_refresh_token,
            oauth_expiration_date=oauth_fields.oauth_expiration_date,
        )
    )
    return await withingsrepository.get_user_by_withings_userid(
        db,
        withings_userid=oauth_fields.oauth_userid,
    )
