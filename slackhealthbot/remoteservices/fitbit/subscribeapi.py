import logging

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.oauth import requests
from slackhealthbot.settings import fitbit_oauth_settings as settings


async def subscribe(
    fitbit_userid: str,
    oauth_token: OAuthFields,
):
    for collectionPath in ["sleep", "activities"]:
        response = await requests.post(
            provider=settings.name,
            token=oauth_token,
            url=f"{settings.base_url}1/user/-/{collectionPath}/apiSubscriptions/{fitbit_userid}-{collectionPath}.json",
        )
        logging.info(
            f"Fitbit {collectionPath} subscription response: {response.json()}"
        )
