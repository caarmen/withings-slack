import datetime

from slackhealthbot.core.models import OAuthFields


def remote_service_oauth_to_core_oauth(response_data: dict) -> OAuthFields:
    return OAuthFields(
        oauth_userid=response_data["userid"],
        oauth_access_token=response_data["access_token"],
        oauth_refresh_token=response_data["refresh_token"],
        oauth_expiration_date=datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(seconds=int(response_data["expires_in"]))
        - datetime.timedelta(minutes=5),
    )
