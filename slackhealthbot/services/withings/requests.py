import httpx
from authlib.integrations.starlette_client.apps import StarletteOAuth2App

from slackhealthbot.database import models as db_models
from slackhealthbot.services.withings import oauth


async def post(
    user: db_models.User,
    url: str,
    data: dict[str, str],
) -> httpx.Response:
    """
    Execute a request, and retry with a refreshed access token if we get a 401.
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    token = {
        "access_token": user.withings.oauth_access_token,
        "refresh_token": user.withings.oauth_refresh_token,
        "expires_at": user.withings.oauth_expiration_date.timestamp(),
    }
    withings: StarletteOAuth2App = oauth.oauth.create_client("withings")
    response = await withings.post(url, data=data, token=token)
    return response
