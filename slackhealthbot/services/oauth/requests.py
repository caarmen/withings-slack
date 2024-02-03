import datetime
from typing import Any, Protocol, runtime_checkable

import httpx
from authlib.integrations.starlette_client.apps import StarletteOAuth2App

from slackhealthbot.services.oauth.config import oauth


@runtime_checkable
class OAuthToken(Protocol):
    oauth_access_token: str
    oauth_refresh_token: str
    oauth_expiration_date: datetime.datetime


def asdict(token: OAuthToken) -> dict[str, str]:
    return {
        "access_token": token.oauth_access_token,
        "refresh_token": token.oauth_refresh_token,
        "expires_at": token.oauth_expiration_date.timestamp(),
    }


async def get(
    provider: str,
    token: OAuthToken,
    url: str,
    params: dict[str, Any] = None,
) -> httpx.Response:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    client: StarletteOAuth2App = oauth.create_client(provider)
    response = await client.get(
        url,
        params=params,
        token=asdict(token),
    )
    return response


async def post(
    provider: str,
    token: OAuthToken,
    url: str,
    data: dict[str, str] = None,
) -> httpx.Response:
    """
    Execute a request, and retry with a refreshed access token if we get a 401.
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    client: StarletteOAuth2App = oauth.create_client(provider)
    response = await client.post(
        url,
        data=data,
        token=asdict(token),
    )
    return response
