import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.database import models as db_models
from slackhealthbot.services.fitbit import oauth


async def request(
    db: AsyncSession,
    user: db_models.User,
    method: str,
    url: str,
    retry_count=1,
) -> httpx.Response:
    """
    Execute a request, and retry with a refreshed access token if we get a 401.
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    oauth_access_token = await oauth.get_access_token(db, user=user)
    headers = {
        "Authorization": f"Bearer {oauth_access_token}",
    }
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, headers=headers)
    if response.status_code == 401 and retry_count > 0:
        await oauth.refresh_token(db, user)
        return await request(db, user, method, url, retry_count - 1)
    return response


async def get(
    db: AsyncSession,
    user: db_models.User,
    url: str,
    retry_count=1,
) -> httpx.Response:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    return await request(db, user, "get", url, retry_count)


async def post(
    db: AsyncSession,
    user: db_models.User,
    url: str,
    retry_count=1,
) -> httpx.Response:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    return await request(db, user, "post", url, retry_count)
