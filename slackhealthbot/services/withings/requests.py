import functools

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.database import models as db_models
from slackhealthbot.services.withings import oauth


def create_headers(oauth_access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {oauth_access_token}",
    }


def requires_oauth(func):
    @functools.wraps(func)
    async def wrapper(
        db: AsyncSession,
        user: db_models.User,
        url: str,
        data: dict[str, str],
    ):
        oauth_access_token = await oauth.get_access_token(db, user=user)
        response: httpx.Response = await func(
            db, user, url, data=data, headers=create_headers(oauth_access_token)
        )
        response_body = response.json()
        if response_body["status"] == 401:
            new_oauth_access_token = await oauth.refresh_token(db, user)
            return await func(
                db, user, url, data=data, headers=create_headers(new_oauth_access_token)
            )
        return response

    return wrapper


@requires_oauth
async def post(
    _db: AsyncSession,
    _user: db_models.User,
    url: str,
    data: dict[str, str],
    headers: dict[str, str] = None,
) -> httpx.Response:
    """
    Execute a request, and retry with a refreshed access token if we get a 401.
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data, headers=headers)
    return response
