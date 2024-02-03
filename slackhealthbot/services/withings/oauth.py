import logging
from typing import Any, Callable

from authlib.common.urls import add_params_to_qs
from authlib.integrations.httpx_client.oauth2_client import AsyncOAuth2Client
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.database import models as db_models
from slackhealthbot.database.connection import ctx_db
from slackhealthbot.services.exceptions import UserLoggedOutException
from slackhealthbot.services.oauth.oauth import oauth
from slackhealthbot.settings import settings

PROVIDER = "withings"


def update_token_wrapper(callback: Callable[[AsyncSession, dict[str, Any]], None]):
    async def update_token(
        token: dict,
        refresh_token=None,
        access_token=None,
        **kwargs,
    ) -> db_models.User:
        db = ctx_db.get()
        await callback(db, token)

    return update_token


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


def configure(update_token_callback: Callable[[AsyncSession, dict[str, Any]], None]):
    oauth.register(
        name=PROVIDER,
        api_base_url=settings.withings_base_url,
        authorize_url="https://account.withings.com/oauth2_user/authorize2",
        access_token_url=f"{settings.withings_base_url}v2/oauth2",
        access_token_params=ACCESS_TOKEN_EXTRA_PARAMS,
        authorize_params={"scope": ",".join(settings.withings_oauth_scopes)},
        compliance_fix=withings_compliance_fix,
        update_token=update_token_wrapper(update_token_callback),
        token_endpoint_auth_method="client_secret_post",
    )
