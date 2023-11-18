import functools
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.database import models as db_models
from slackhealthbot.services.fitbit import oauth


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
        **kwargs,
    ):
        oauth_access_token = await oauth.get_access_token(db, user=user)
        response: httpx.Response = await func(
            db, user, url, headers=create_headers(oauth_access_token), **kwargs
        )
        if response.status_code == 401:
            new_oauth_access_token = await oauth.refresh_token(db, user)
            return await func(
                db, user, url, headers=create_headers(new_oauth_access_token), **kwargs
            )
        return response

    return wrapper


@requires_oauth
async def get(
    _db: AsyncSession,
    _user: db_models.User,
    url: str,
    params: dict[str, Any] = None,
    headers: dict[str, str] = None,
) -> httpx.Response:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    async with httpx.AsyncClient() as client:
        return await client.get(url, params=params, headers=headers)


@requires_oauth
async def post(
    _db: AsyncSession,
    _user: db_models.User,
    url: str,
    headers: dict[str, str] = None,
) -> httpx.Response:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    async with httpx.AsyncClient() as client:
        return await client.post(url, headers=headers)
