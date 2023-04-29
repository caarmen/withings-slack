import dataclasses
import datetime
import hashlib
import hmac
import random
import string
from typing import Optional, Self
from urllib.parse import urlencode

import requests
from pydantic import HttpUrl
from sqlalchemy.orm import Session

from withingsslack.database import crud
from withingsslack.database import models as db_models
from withingsslack.services import models as svc_models
from withingsslack.settings import settings


@dataclasses.dataclass
class MemorySettings:
    oauth_state_to_slack_alias: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class OauthFields:
    oauth_access_token: str
    oauth_refresh_token: str
    oauth_expiration_date: datetime

    @classmethod
    def parse_response_data(cls, response_data: dict) -> Self:
        return cls(
            oauth_access_token=response_data["access_token"],
            oauth_refresh_token=response_data["refresh_token"],
            oauth_expiration_date=datetime.datetime.utcnow()
            + datetime.timedelta(seconds=response_data["expires_in"]),
        )


_settings = MemorySettings()


def _create_signature_request_payload() -> str:
    action = "getnonce"
    client_id = settings.withings_client_id
    timestamp = int(datetime.datetime.now().timestamp())
    data = f"{action},{client_id},{timestamp}"
    signature = hmac.new(
        bytearray(settings.withings_client_secret.encode("utf-8")),
        bytearray(data.encode("utf-8")),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return {
        "action": action,
        "client_id": client_id,
        "timestamp": timestamp,
        "signature": signature,
    }


def get_nonce() -> str:
    response = requests.post(
        f"{settings.withings_base_url}v2/signature/",
        data=_create_signature_request_payload(),
    )
    response_content = response.json()
    return response_content["body"]["nonce"]


def create_oauth_url(slack_alias: str) -> HttpUrl:
    state = "".join(random.choices(string.ascii_lowercase, k=16))
    _settings.oauth_state_to_slack_alias[state] = slack_alias
    url = "https://account.withings.com/oauth2_user/authorize2"
    query_params = {
        "client_id": settings.withings_client_id,
        "redirect_uri": settings.withings_oauth_redirect_url,
        "response_type": "code",
        "scope": ",".join(settings.withings_oauth_scopes),
        "state": state,
    }
    return f"{url}?{urlencode(query_params)}"


def fetch_token(db: Session, state: str, code: str) -> db_models.User:
    slack_alias = _settings.oauth_state_to_slack_alias.pop(state, None)
    if not slack_alias:
        raise ValueError("Invalid state parameter")
    response = requests.post(
        f"{settings.withings_base_url}v2/oauth2",
        data={
            "action": "requesttoken",
            "client_id": settings.withings_client_id,
            "client_secret": settings.withings_client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.withings_oauth_redirect_url,
        },
    )
    response_data = response.json()["body"]
    oauth_userid = response_data["userid"]
    oauth_fields = OauthFields.parse_response_data(response_data)
    user = crud.get_or_create_user(db, oauth_userid=oauth_userid)
    crud.update_user(
        db,
        user=user,
        data={
            "slack_alias": slack_alias,
            **dataclasses.asdict(oauth_fields),
        },
    )
    return user


def get_access_token(db: Session, user: db_models.User) -> str:
    if user.oauth_expiration_date < datetime.datetime.utcnow():
        refresh_token(db, user)
    return user.oauth_access_token


def refresh_token(db: Session, user: db_models.User):
    print(f"Refreshing access token for {user.slack_alias}")
    response = requests.post(
        f"{settings.withings_base_url}v2/oauth2",
        data={
            "action": "requesttoken",
            "client_id": settings.withings_client_id,
            "client_secret": settings.withings_client_secret,
            "grant_type": "refresh_token",
            "refresh_token": user.oauth_refresh_token,
        },
    )
    response_data = response.json()["body"]
    oauth_fields = OauthFields.parse_response_data(response_data)
    crud.update_user(
        db,
        user=user,
        data=dataclasses.asdict(oauth_fields),
    )


def subscribe(user: db_models.User):
    # https://developer.withings.com/api-reference#tag/notify/operation/notify-subscribe
    response = requests.post(
        url=f"{settings.withings_base_url}notify",
        headers={
            "Authorization": f"Bearer {user.oauth_access_token}",
        },
        data={
            "action": "subscribe",
            "callbackurl": str(settings.withings_notification_callback_url),
            "appli": 1,
        },
    )
    print(f"Subscription response: {response.json()}")


def get_last_weight(
    db: Session,
    userid: str,
    startdate: int,
    enddate: int,
) -> Optional[svc_models.WeightData]:
    # https://developer.withings.com/api-reference/#tag/measure/operation/measure-getmeas
    user = crud.get_user(db, oauth_userid=userid)
    oauth_access_token = get_access_token(db, user=user)
    response = requests.post(
        url=f"{settings.withings_base_url}measure",
        headers={
            "Authorization": f"Bearer {oauth_access_token}",
        },
        data={
            "action": "getmeas",
            "meastype": 1,  # weight
            "category": 1,  # real measures, not objectives
            "startdate": startdate,
            "enddate": enddate,
        },
    )
    response_data = response.json()["body"]
    measuregrps = response_data["measuregrps"]
    if measuregrps:
        last_measuregrp_item = measuregrps[-1]
        measures = last_measuregrp_item["measures"]
        if measures:
            last_measure = measures[0]
            weight_kg = last_measure["value"] * pow(10, last_measure["unit"])
            measure_date = datetime.datetime.fromtimestamp(last_measuregrp_item["date"])
            return svc_models.WeightData(
                weight_kg=weight_kg,
                date=measure_date,
                slack_alias=user.slack_alias,
            )
    return None
