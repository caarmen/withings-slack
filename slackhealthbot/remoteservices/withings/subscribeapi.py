import logging

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
