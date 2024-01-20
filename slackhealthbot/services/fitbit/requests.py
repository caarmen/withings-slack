from typing import Any

import httpx
from authlib.integrations.starlette_client.apps import StarletteOAuth2App

from slackhealthbot.database import models as db_models
from slackhealthbot.services.fitbit import oauth


async def get(
    user: db_models.User,
    url: str,
    params: dict[str, Any] = None,
) -> httpx.Response:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    token = {
        "access_token": user.fitbit.oauth_access_token,
        "refresh_token": user.fitbit.oauth_refresh_token,
        "expires_at": user.fitbit.oauth_expiration_date.timestamp(),
    }
    fitbit: StarletteOAuth2App = oauth.oauth.create_client("fitbit")
    response = await fitbit.get(url, params=params, token=token)
    return response


async def post(
    user: db_models.User,
    url: str,
) -> httpx.Response:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    token = {
        "access_token": user.fitbit.oauth_access_token,
        "refresh_token": user.fitbit.oauth_refresh_token,
        "expires_at": user.fitbit.oauth_expiration_date.timestamp(),
    }
    fitbit: StarletteOAuth2App = oauth.oauth.create_client("fitbit")
    response = await fitbit.post(url, token=token)
    return response
