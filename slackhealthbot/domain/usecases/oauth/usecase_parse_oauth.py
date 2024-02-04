import datetime

from slackhealthbot.core.models import OAuthFields


def do(response_data: dict) -> OAuthFields:
    return OAuthFields(
        oauth_userid=response_data["userid"],
        oauth_access_token=response_data["access_token"],
        oauth_refresh_token=response_data["refresh_token"],
        oauth_expiration_date=datetime.datetime.utcnow()
        + datetime.timedelta(seconds=response_data["expires_in"])
        - datetime.timedelta(minutes=5),
    )
