import dataclasses
import logging

from authlib.common.urls import add_params_to_qs
from authlib.integrations.httpx_client.oauth2_client import AsyncOAuth2Client
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.database import crud
from slackhealthbot.database import models as db_models
from slackhealthbot.database.connection import ctx_db
from slackhealthbot.services.exceptions import UserLoggedOutException
from slackhealthbot.services.oauth.oauth import OAuthFields, oauth
from slackhealthbot.settings import settings

PROVIDER = "withings"


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
            withings_oauth_userid=oauth_fields.oauth_userid,
            data=kwargs,
            withings_data=dataclasses.asdict(oauth_fields),
        ),
    )


ACCESS_TOKEN_EXTRA_PARAMS = {
    "action": "requesttoken",
}


def withings_compliance_fix(session: AsyncOAuth2Client):
    def _fix_refresh_token_request(url, headers, body):
        body = add_params_to_qs(body, ACCESS_TOKEN_EXTRA_PARAMS)
        return url, headers, body

    def _fix_access_token_response(resp):
        data = resp.json()
        logging.info(f"Token response {data}")
        # https://developer.withings.com/api-reference/#section/Response-status
        if data["status"] != 0:
            resp.status_code = 400
            raise UserLoggedOutException
        resp.json = lambda: data["body"]
        return resp

    session.register_compliance_hook(
        "refresh_token_request", _fix_refresh_token_request
    )
    session.register_compliance_hook(
        "refresh_token_response", _fix_access_token_response
    )
    session.register_compliance_hook(
        "access_token_response", _fix_access_token_response
    )


oauth.register(
    name=PROVIDER,
    api_base_url=settings.withings_base_url,
    authorize_url="https://account.withings.com/oauth2_user/authorize2",
    access_token_url=f"{settings.withings_base_url}v2/oauth2",
    access_token_params=ACCESS_TOKEN_EXTRA_PARAMS,
    authorize_params={"scope": ",".join(settings.withings_oauth_scopes)},
    compliance_fix=withings_compliance_fix,
    update_token=update_token,
    token_endpoint_auth_method="client_secret_post",
)
