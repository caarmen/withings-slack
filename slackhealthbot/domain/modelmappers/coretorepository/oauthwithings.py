from slackhealthbot.core.models import OAuthFields
from slackhealthbot.data.repositories import withingsrepository


def core_oauth_to_repository_oauth(
    core: OAuthFields,
) -> withingsrepository.OAuthData:
    return withingsrepository.OAuthData(
        oauth_access_token=core.oauth_access_token,
        oauth_refresh_token=core.oauth_refresh_token,
        oauth_expiration_date=core.oauth_expiration_date,
    )
