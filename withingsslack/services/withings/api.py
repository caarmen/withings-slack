import datetime
import logging
from typing import Optional

from sqlalchemy.orm import Session

from withingsslack.database import crud
from withingsslack.database import models as db_models
from withingsslack.services import models as svc_models
from withingsslack.settings import settings
from withingsslack.services.withings import requests


def subscribe(db: Session, user: db_models.User):
    callbackurl = f"{settings.withings_callback_url}withings-notification-webhook/"
    # https://developer.withings.com/api-reference#tag/notify/operation/notify-subscribe
    response = requests.post(
        db,
        user=user,
        url=f"{settings.withings_base_url}notify",
        data={
            "action": "subscribe",
            "callbackurl": callbackurl,
            "appli": 1,
        },
    )
    logging.info(f"Subscription response: {response.json()}")


def get_last_weight(
    db: Session,
    userid: str,
    startdate: int,
    enddate: int,
) -> Optional[svc_models.WeightData]:
    # https://developer.withings.com/api-reference/#tag/measure/operation/measure-getmeas
    user = crud.get_user(db, oauth_userid=userid)
    response = requests.post(
        db,
        user=user,
        url=f"{settings.withings_base_url}measure",
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
        last_measuregrp_item = measuregrps[0]
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
