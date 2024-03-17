import datetime
from abc import ABC

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.models.activity import ActivityData
from slackhealthbot.domain.models.sleep import SleepData


class RemoteFitbitRepository(ABC):
    async def subscribe(
        self,
        oauth_fields: OAuthFields,
    ):
        pass

    async def get_activity(
        self, oauth_fields: OAuthFields, when: datetime.datetime
    ) -> tuple[str, ActivityData] | None:
        pass

    async def get_sleep(
        self,
        oauth_fields: OAuthFields,
        when: datetime.date,
    ) -> SleepData | None:
        pass

    def parse_oauth_fields(
        self,
        response_data: dict[str, str],
    ) -> OAuthFields:
        pass
