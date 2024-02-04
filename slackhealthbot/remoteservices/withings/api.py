import logging
from typing import Optional

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.oauth import requests
from slackhealthbot.settings import withings_oauth_settings as settings


async def subscribe(
    oauth_token: OAuthFields,
):
    callbackurl = f"{settings.callback_url}withings-notification-webhook/"
    # https://developer.withings.com/api-reference#tag/notify/operation/notify-subscribe
    response = await requests.post(
        provider=settings.name,
        token=oauth_token,
        url=f"{settings.base_url}notify",
        data={
            "action": "subscribe",
            "callbackurl": callbackurl,
            "appli": 1,
        },
    )
    logging.info(f"Withings subscription response: {response.json()}")


async def get_last_weight_kg(
    oauth_token: OAuthFields,
    startdate: int,
    enddate: int,
) -> Optional[float]:
    """
    :raises:
        UserLoggedOutException if the refresh token request fails
    """
    # https://developer.withings.com/api-reference/#tag/measure/operation/measure-getmeas
    response = await requests.post(
        provider=settings.name,
        token=oauth_token,
        url=f"{settings.base_url}measure",
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
            return weight_kg
    return None
