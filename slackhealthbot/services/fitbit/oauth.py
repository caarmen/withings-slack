import dataclasses
import logging

from authlib.integrations.httpx_client.oauth2_client import AsyncOAuth2Client
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.database import crud
from slackhealthbot.database import models as db_models
from slackhealthbot.database.connection import ctx_db
from slackhealthbot.services.exceptions import UserLoggedOutException
from slackhealthbot.services.oauth.oauth import OAuthFields, oauth
from slackhealthbot.settings import settings

PROVIDER = "fitbit"


async def update_token(
    token: dict,
    refresh_token=None,
    access_token=None,
    db: AsyncSession = None,
    **kwargs,
) -> db_models.User:
    if not db:
        db = ctx_db.get()
    oauth_fields = OAuthFields.parse_response_data(token)
    return await crud.upsert_user(
        db,
        crud.UserUpsert(
            fitbit_oauth_userid=oauth_fields.oauth_userid,
            data=kwargs,
            fitbit_data=dataclasses.asdict(oauth_fields),
        ),
    )


def fitbit_compliance_fix(session: AsyncOAuth2Client):
    def _fix_access_token_response(resp):
        data = resp.json()
        logging.info(f"Token response {data}")
        if resp.status_code != status.HTTP_200_OK:
            raise UserLoggedOutException
        data["userid"] = data["user_id"]
        resp.json = lambda: data
        return resp

    session.register_compliance_hook(
        "refresh_token_response", _fix_access_token_response
    )
    session.register_compliance_hook(
        "access_token_response", _fix_access_token_response
    )


oauth.register(
    name=PROVIDER,
    api_base_url=settings.fitbit_base_url,
    authorize_url="https://www.fitbit.com/oauth2/authorize",
    access_token_url=f"{settings.fitbit_base_url}oauth2/token",
    authorize_params={"scope": " ".join(settings.fitbit_oauth_scopes)},
    compliance_fix=fitbit_compliance_fix,
    update_token=update_token,
    token_endpoint_auth_method="client_secret_basic",
    client_kwargs={"code_challenge_method": "S256"},
)
