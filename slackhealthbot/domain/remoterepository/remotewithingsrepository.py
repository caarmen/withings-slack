from abc import ABC, abstractmethod

from slackhealthbot.core.models import OAuthFields


class RemoteWithingsRepository(ABC):

    @abstractmethod
    async def subscribe(
        self,
        oauth_fields: OAuthFields,
    ):
        pass

    @abstractmethod
    async def get_last_weight_kg(
        self,
        oauth_fields: OAuthFields,
        startdate: int,
        enddate: int,
    ) -> float | None:
        pass

    @abstractmethod
    def parse_oauth_fields(
        self,
        response_data: dict[str, str],
    ) -> OAuthFields:
        pass
