from abc import ABC

from slackhealthbot.core.models import OAuthFields


class RemoteWithingsRepository(ABC):

    async def subscribe(
        self,
        oauth_fields: OAuthFields,
    ):
        pass

    async def get_last_weight_kg(
        self,
        oauth_fields: OAuthFields,
        startdate: int,
        enddate: int,
    ) -> float | None:
        pass
