from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.oauth import usecase_parse_oauth
from slackhealthbot.repositories import fitbitrepository
from slackhealthbot.repositories.fitbitrepository import OAuthData, UserIdentity
from slackhealthbot.services.fitbit import api


async def do(
    db: AsyncSession,
    slack_alias: str,
    token: dict[str, Any],
):
    user: fitbitrepository.User = await _upsert_user(db, slack_alias, token)
    await api.subscribe(
        fitbit_userid=user.identity.fitbit_userid, oauth_token=user.oauth_data
    )


async def _upsert_user(
    db: AsyncSession, slack_alias: str, token: dict[str, Any]
) -> fitbitrepository.User:
    oauth_fields: OAuthFields = usecase_parse_oauth.do(token)
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
            oauth_access_token=oauth_fields.oauth_access_token,
            oauth_refresh_token=oauth_fields.oauth_refresh_token,
            oauth_expiration_date=oauth_fields.oauth_expiration_date,
        )
    await fitbitrepository.update_oauth_data(
        db,
        fitbit_userid=oauth_fields.oauth_userid,
        oauth_data=OAuthData(
            oauth_access_token=oauth_fields.oauth_access_token,
            oauth_refresh_token=oauth_fields.oauth_refresh_token,
            oauth_expiration_date=oauth_fields.oauth_expiration_date,
        ),
    )
    return await fitbitrepository.get_user_by_fitbit_userid(
        db,
        fitbit_userid=oauth_fields.oauth_userid,
    )
