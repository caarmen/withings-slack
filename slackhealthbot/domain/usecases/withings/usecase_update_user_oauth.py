from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.database.connection import ctx_db
from slackhealthbot.domain.modelmappers.coretorepository.oauthwithings import (
    core_oauth_to_repository_oauth,
)
from slackhealthbot.domain.modelmappers.remoteservicetocore import oauth
from slackhealthbot.repositories import withingsrepository


async def do(
    token: dict[str, Any],
    **_kwargs,
):
    db: AsyncSession = ctx_db.get()
    oauth_fields: OAuthFields = oauth.remote_service_oauth_to_core_oauth(token)
    await withingsrepository.update_oauth_data(
        db,
        withings_userid=oauth_fields.oauth_userid,
        oauth_data=core_oauth_to_repository_oauth(oauth_fields),
    )
