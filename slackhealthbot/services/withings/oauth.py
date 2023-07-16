import dataclasses
import datetime
import logging
import random
import string
from typing import Self
from urllib.parse import urlencode

import httpx
from pydantic import HttpUrl
from sqlalchemy.orm import Session

from slackhealthbot.database import crud
from slackhealthbot.database import models as db_models
from slackhealthbot.services.exceptions import UserLoggedOutException
from slackhealthbot.services.withings import signing
from slackhealthbot.settings import settings


@dataclasses.dataclass
class MemorySettings:
    oauth_state_to_slack_alias: dict[str, str] = dataclasses.field(default_factory=dict)


_settings = MemorySettings()


@dataclasses.dataclass
class OauthFields:
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
            + datetime.timedelta(seconds=response_data["expires_in"]),
        )


def create_oauth_url(slack_alias: str) -> HttpUrl:
    state = "".join(random.choices(string.ascii_lowercase, k=16))
    _settings.oauth_state_to_slack_alias[state] = slack_alias
    url = "https://account.withings.com/oauth2_user/authorize2"
    query_params = {
        "client_id": settings.withings_client_id,
        "redirect_uri": f"{settings.withings_callback_url}withings-oauth-webhook/",
        "response_type": "code",
        "scope": ",".join(settings.withings_oauth_scopes),
        "state": state,
    }
    return f"{url}?{urlencode(query_params)}"


def fetch_token(db: Session, state: str, code: str) -> db_models.User:
    slack_alias = _settings.oauth_state_to_slack_alias.pop(state, None)
    if not slack_alias:
        raise ValueError("Invalid state parameter")
    response = httpx.post(
        f"{settings.withings_base_url}v2/oauth2",
        data={
            "action": "requesttoken",
            "client_id": settings.withings_client_id,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": f"{settings.withings_callback_url}withings-oauth-webhook/",
            **signing.sign_action("requesttoken"),
        },
    )
    response_data = response.json()["body"]
    oauth_userid = response_data["userid"]
    oauth_fields = OauthFields.parse_response_data(response_data)
    user = crud.upsert_user(
        db,
        withings_oauth_userid=oauth_userid,
        data={"slack_alias": slack_alias},
        withings_data=dataclasses.asdict(oauth_fields),
    )
    return user


def get_access_token(db: Session, user: db_models.User) -> str:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    if (
        not user.withings.oauth_expiration_date
        or user.withings.oauth_expiration_date < datetime.datetime.utcnow()
    ):
        refresh_token(db, user)
    return user.withings.oauth_access_token


def refresh_token(db: Session, user: db_models.User) -> str:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    logging.info(f"Refreshing withings access token for {user.slack_alias}")
    response = httpx.post(
        f"{settings.withings_base_url}v2/oauth2",
        data={
            "action": "requesttoken",
            "client_id": settings.withings_client_id,
            "grant_type": "refresh_token",
            "refresh_token": user.withings.oauth_refresh_token,
            **signing.sign_action("requesttoken"),
        },
    )

    response_data = response.json()
    logging.info(f"Refresh token response {response_data}")
    # https://developer.withings.com/api-reference/#section/Response-status
    if response_data["status"] != 0:
        raise UserLoggedOutException
    oauth_fields = OauthFields.parse_response_data(response_data["body"])
    user = crud.update_user(
        db,
        user=user,
        withings_data=dataclasses.asdict(oauth_fields),
    )
    return user.withings.oauth_access_token
