import dataclasses
import datetime
import logging
from typing import Self

from authlib.common.urls import add_params_to_qs
from authlib.integrations.httpx_client.oauth2_client import AsyncOAuth2Client
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client.apps import StarletteOAuth2App
from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.config import Config

from slackhealthbot.database import crud
from slackhealthbot.database import models as db_models
from slackhealthbot.database.connection import ctx_db
from slackhealthbot.services.exceptions import UserLoggedOutException
from slackhealthbot.settings import settings


async def update_token(token: dict, refresh_token=None, access_token=None):
    oauth_fields = OauthFields.parse_response_data(token)
    db = ctx_db.get()
    await crud.upsert_user(
        db,
        crud.UserUpsert(
            withings_oauth_userid=oauth_fields.oauth_userid,
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


config = Config(".env")
oauth = OAuth(config)
oauth.register(
    name="withings",
    api_base_url=settings.withings_base_url,
    authorize_url="https://account.withings.com/oauth2_user/authorize2",
    access_token_url=f"{settings.withings_base_url}v2/oauth2",
    access_token_params=ACCESS_TOKEN_EXTRA_PARAMS,
    authorize_params={"scope": ",".join(settings.withings_oauth_scopes)},
    compliance_fix=withings_compliance_fix,
    update_token=update_token,
    token_endpoint_auth_method="client_secret_post",
)


@dataclasses.dataclass
class OauthFields:
    oauth_userid: str
    oauth_access_token: str
    oauth_refresh_token: str
    oauth_expiration_date: datetime

    @classmethod
    def parse_response_data(cls, response_data: dict) -> Self:
        return cls(
            oauth_userid=response_data["userid"],
            oauth_access_token=response_data["access_token"],
            oauth_refresh_token=response_data["refresh_token"],
            oauth_expiration_date=datetime.datetime.utcnow()
            + datetime.timedelta(seconds=response_data["expires_in"])
            - datetime.timedelta(minutes=5),
        )


async def create_oauth_url(request: Request, slack_alias: str) -> RedirectResponse:
    request.session["slack_alias"] = slack_alias
    withings: StarletteOAuth2App = oauth.create_client("withings")
    return await withings.authorize_redirect(
        request,
        redirect_uri=f"{settings.withings_callback_url}withings-oauth-webhook/",
    )


async def fetch_token(db: AsyncSession, request: Request) -> db_models.User:
    withings: StarletteOAuth2App = oauth.create_client("withings")
    response = await withings.authorize_access_token(request)
    oauth_fields = OauthFields.parse_response_data(response)
    user = await crud.upsert_user(
        db,
        crud.UserUpsert(
            withings_oauth_userid=response["userid"],
            data={"slack_alias": request.session.pop("slack_alias")},
            withings_data=dataclasses.asdict(oauth_fields),
        ),
    )
    return user
