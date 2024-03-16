from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.remoterepository.remotewithingsrepository import (
    RemoteWithingsRepository,
)
from slackhealthbot.remoteservices.api.withings import subscribeapi, weightapi


class WebApiWithingsRepository(RemoteWithingsRepository):
    async def subscribe(
        self,
        oauth_fields: OAuthFields,
    ):
        await subscribeapi.subscribe(oauth_fields)

    async def get_last_weight_kg(
        self,
        oauth_fields: OAuthFields,
        startdate: int,
        enddate: int,
    ) -> float | None:
        return await weightapi.get_last_weight_kg(
            oauth_token=oauth_fields,
            startdate=startdate,
            enddate=enddate,
        )
