import dataclasses
import datetime
from abc import ABC

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.models.activity import ActivityData, TopActivityStats
from slackhealthbot.domain.models.sleep import SleepData


@dataclasses.dataclass
class UserIdentity:
    fitbit_userid: str
    slack_alias: str


@dataclasses.dataclass
class User:
    identity: UserIdentity
    oauth_data: OAuthFields


class FitbitRepository(ABC):
    async def create_user(
        self,
        slack_alias: str,
        fitbit_userid: str,
        oauth_data: OAuthFields,
    ) -> User:
        pass

    async def get_user_identity_by_fitbit_userid(
        self,
        fitbit_userid: str,
    ) -> UserIdentity | None:
        pass

    async def get_all_user_identities(self) -> list[UserIdentity]:
        pass

    async def get_oauth_data_by_fitbit_userid(
        self,
        fitbit_userid: str,
    ) -> OAuthFields:
        pass

    async def get_user_by_fitbit_userid(
        self,
        fitbit_userid: str,
    ) -> User:
        pass

    async def get_latest_activity_by_user_and_type(
        self,
        fitbit_userid: str,
        type_id: int,
    ) -> ActivityData | None:
        pass

    async def get_activity_by_user_and_log_id(
        self,
        fitbit_userid: str,
        log_id: int,
    ) -> ActivityData | None:
        pass

    async def create_activity_for_user(
        self,
        fitbit_userid: str,
        activity: ActivityData,
    ):
        pass

    async def update_sleep_for_user(
        self,
        fitbit_userid: str,
        sleep: SleepData,
    ):
        pass

    async def get_sleep_by_fitbit_userid(
        self,
        fitbit_userid: str,
    ) -> SleepData | None:
        pass

    async def update_oauth_data(
        self,
        fitbit_userid: str,
        oauth_data: OAuthFields,
    ):
        pass

    async def get_top_activity_stats_by_user_and_activity_type(
        self,
        fitbit_userid: str,
        type_id: int,
        since: datetime.datetime | None = None,
    ) -> TopActivityStats:
        pass
