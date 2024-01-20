import dataclasses
import datetime
from typing import Self

from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client.apps import StarletteOAuth2App
from fastapi import Request
from pydantic import HttpUrl
from starlette.config import Config

config = Config(".env")
oauth = OAuth(config)


@dataclasses.dataclass
class OAuthFields:
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


async def create_oauth_url(
    provider: str, request: Request, slack_alias: str, **kwargs
) -> HttpUrl:
    request.session["slack_alias"] = slack_alias
    client: StarletteOAuth2App = oauth.create_client(provider)
    return await client.authorize_redirect(request, **kwargs)


async def fetch_token(provider: str, request: Request) -> dict:
    return await oauth.create_client(provider).authorize_access_token(request)
