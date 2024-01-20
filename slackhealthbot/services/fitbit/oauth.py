import dataclasses
import datetime
import logging
from typing import Self

from authlib.integrations.httpx_client.oauth2_client import AsyncOAuth2Client
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client.apps import StarletteOAuth2App
from fastapi import Request, status
from pydantic import HttpUrl
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
        fitbit_oauth_userid=oauth_fields.oauth_userid,
        fitbit_data=dataclasses.asdict(oauth_fields),
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


config = Config(".env")
oauth = OAuth(config)
oauth.register(
    name="fitbit",
    api_base_url=settings.fitbit_base_url,
    authorize_url="https://www.fitbit.com/oauth2/authorize",
    access_token_url=f"{settings.fitbit_base_url}oauth2/token",
    authorize_params={"scope": " ".join(settings.fitbit_oauth_scopes)},
    compliance_fix=fitbit_compliance_fix,
    update_token=update_token,
    token_endpoint_auth_method="client_secret_basic",
    client_kwargs={"code_challenge_method": "S256"},
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
            oauth_userid=response_data["user_id"],
            oauth_access_token=response_data["access_token"],
            oauth_refresh_token=response_data["refresh_token"],
            oauth_expiration_date=datetime.datetime.utcnow()
            + datetime.timedelta(seconds=response_data["expires_in"])
            - datetime.timedelta(minutes=5),
        )


async def create_oauth_url(request: Request, slack_alias: str) -> HttpUrl:
    request.session["slack_alias"] = slack_alias
    fitbit: StarletteOAuth2App = oauth.create_client("fitbit")
    return await fitbit.authorize_redirect(
        request,
    )


async def fetch_token(db: AsyncSession, request: Request) -> db_models.User:
    fitbit: StarletteOAuth2App = oauth.create_client("fitbit")
    response = await fitbit.authorize_access_token(request)
    oauth_fields = OauthFields.parse_response_data(response)
    user = await crud.upsert_user(
        db,
        fitbit_oauth_userid=response["userid"],
        data={"slack_alias": request.session.pop("slack_alias")},
        fitbit_data=dataclasses.asdict(oauth_fields),
    )
    return user
