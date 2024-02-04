from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.database.connection import ctx_db
from slackhealthbot.domain.modelmappers.coretorepository.oauthfitbit import (
    core_oauth_to_repository_oauth,
)
from slackhealthbot.domain.usecases.oauth import usecase_parse_oauth
from slackhealthbot.repositories import fitbitrepository


async def do(
    token: dict[str, Any],
    **_kwargs,
):
    db: AsyncSession = ctx_db.get()
    oauth_fields: OAuthFields = usecase_parse_oauth.do(token)
    await fitbitrepository.update_oauth_data(
        db,
        fitbit_userid=oauth_fields.oauth_userid,
        oauth_data=core_oauth_to_repository_oauth(oauth_fields),
    )
