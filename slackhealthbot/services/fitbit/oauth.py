import dataclasses
import datetime
import hashlib
import logging
import random
import string
from base64 import urlsafe_b64encode
from typing import Optional, Self
from urllib.parse import urlencode

import httpx
from pydantic import HttpUrl
from sqlalchemy.orm import Session

from slackhealthbot.database import crud
from slackhealthbot.database import models as db_models
from slackhealthbot.services.exceptions import UserLoggedOutException
from slackhealthbot.settings import settings


@dataclasses.dataclass
class State:
    code_verifier: str
    slack_alias: str

    @property
    def code_challenge(self) -> Optional[str]:
        m = hashlib.sha256()
        m.update(self.code_verifier.encode("utf-8"))
        return urlsafe_b64encode(m.digest()).decode("utf-8").strip("=")


@dataclasses.dataclass
class MemorySettings:
    oauth_states: dict[str, State] = dataclasses.field(default_factory=dict)


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
            oauth_userid=response_data["user_id"],
            oauth_access_token=response_data["access_token"],
            oauth_refresh_token=response_data["refresh_token"],
            oauth_expiration_date=datetime.datetime.utcnow()
            + datetime.timedelta(seconds=response_data["expires_in"]),
        )


def _authorization_headers():
    authorization = urlsafe_b64encode(
        f"{settings.fitbit_client_id}:{settings.fitbit_client_secret}".encode("utf-8")
    ).decode("utf-8")
    return {
        "Authorization": f"Basic {authorization}",
    }


def create_oauth_url(slack_alias: str) -> HttpUrl:
    url = "https://www.fitbit.com/oauth2/authorize"
    state_key = "".join(random.choices(string.ascii_lowercase, k=16))
    state_value = State(
        code_verifier="".join(random.choices(string.ascii_lowercase, k=100)),
        slack_alias=slack_alias,
    )
    _settings.oauth_states[state_key] = state_value

    query_params = {
        "client_id": settings.fitbit_client_id,
        "response_type": "code",
        "code_challenge": state_value.code_challenge,
        "code_challenge_method": "S256",
        "scope": " ".join(settings.fitbit_oauth_scopes),
        "state": state_key,
    }
    return f"{url}?{urlencode(query_params)}"


def fetch_token(db: Session, code: str, state: str) -> db_models.User:
    state_value = _settings.oauth_states.pop(state, None)
    if not state_value:
        raise ValueError("Invalid state parameter")
    response = httpx.post(
        f"{settings.fitbit_base_url}oauth2/token",
        headers=_authorization_headers(),
        data={
            "client_id": settings.fitbit_client_id,
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": state_value.code_verifier,
        },
    )
    response_data = response.json()
    oauth_userid = response_data["user_id"]
    oauth_fields = OauthFields.parse_response_data(response_data)
    user = crud.upsert_user(
        db,
        fitbit_oauth_userid=oauth_userid,
        data={"slack_alias": state_value.slack_alias},
        fitbit_data=dataclasses.asdict(oauth_fields),
    )
    return user


def get_access_token(db: Session, user: db_models.User) -> str:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    if (
        not user.fitbit.oauth_expiration_date
        or user.fitbit.oauth_expiration_date < datetime.datetime.utcnow()
    ):
        refresh_token(db, user)
    return user.fitbit.oauth_access_token


def refresh_token(db: Session, user: db_models.User) -> str:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    logging.info(f"Refreshing fitbit access token for {user.slack_alias}")
    response = httpx.post(
        f"{settings.fitbit_base_url}oauth2/token",
        headers=_authorization_headers(),
        data={
            "client_id": settings.fitbit_client_id,
            "grant_type": "refresh_token",
            "refresh_token": user.fitbit.oauth_refresh_token,
        },
    )
    response_data = response.json()
    if response.status_code != 200:
        raise UserLoggedOutException
    oauth_fields = OauthFields.parse_response_data(response_data)
    user = crud.update_user(
        db,
        user=user,
        fitbit_data=dataclasses.asdict(oauth_fields),
    )
    return user.fitbit.oauth_access_token
