import requests
from sqlalchemy.orm import Session

from withingsslack.database import models as db_models
from withingsslack.services.fitbit import oauth


def request(
    db: Session,
    user: db_models.User,
    method: str,
    url: str,
    retry_count=1,
) -> requests.Response:
    """
    Execute a request, and retry with a refreshed access token if we get a 401.
    """
    oauth_access_token = oauth.get_access_token(db, user=user)
    headers = {
        "Authorization": f"Bearer {oauth_access_token}",
    }
    response = requests.request(method, url, headers=headers)
    if response.status_code == 401 and retry_count > 0:
        oauth.refresh_token(db, user)
        return request(db, user, method, url, retry_count - 1)
    return response


def get(
    db: Session,
    user: db_models.User,
    url: str,
    retry_count=1,
) -> requests.Response:
    return request(db, user, "get", url, retry_count)


def post(
    db: Session,
    user: db_models.User,
    url: str,
    retry_count=1,
) -> requests.Response:
    return request(db, user, "post", url, retry_count)
