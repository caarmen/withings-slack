import httpx
from sqlalchemy.orm import Session

from slackhealthbot.database import models as db_models
from slackhealthbot.services.withings import oauth


def post(
    db: Session,
    user: db_models.User,
    url: str,
    data: dict[str, str],
    retry_count=1,
) -> httpx.Response:
    """
    Execute a request, and retry with a refreshed access token if we get a 401.
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    oauth_access_token = oauth.get_access_token(db, user=user)
    headers = {
        "Authorization": f"Bearer {oauth_access_token}",
    }
    response = httpx.post(url, headers=headers, data=data)
    response_body = response.json()
    if response_body["status"] == 401 and retry_count > 0:
        oauth.refresh_token(db, user)
        return post(db, user, url, data, retry_count - 1)
    return response
