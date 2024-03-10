import dataclasses
from abc import ABC, abstractmethod

from slackhealthbot.core.models import OAuthFields


@dataclasses.dataclass
class UserIdentity:
    withings_userid: str
    slack_alias: str


@dataclasses.dataclass
class FitnessData:
    last_weight_kg: float | None = None


@dataclasses.dataclass
class User:
    identity: UserIdentity
    oauth_data: OAuthFields
    fitness_data: FitnessData


class WithingsRepository(ABC):
    @abstractmethod
    async def create_user(
        self,
        slack_alias: str,
        withings_userid: str,
        oauth_data: OAuthFields,
    ) -> User:
        pass

    @abstractmethod
    async def get_user_identity_by_withings_userid(
        self,
        withings_userid: str,
    ) -> UserIdentity | None:
        pass

    @abstractmethod
    async def get_oauth_data_by_withings_userid(
        self,
        withings_userid: str,
    ) -> OAuthFields:
        pass

    @abstractmethod
    async def get_fitness_data_by_withings_userid(
        self,
        withings_userid: str,
    ) -> FitnessData:
        pass

    @abstractmethod
    async def get_user_by_withings_userid(
        self,
        withings_userid: str,
    ) -> User:
        pass

    @abstractmethod
    async def update_user_weight(
        self,
        withings_userid: str,
        last_weight_kg: float,
    ):
        pass

    async def update_oauth_data(
        self,
        withings_userid: str,
        oauth_data: OAuthFields,
    ):
        pass
