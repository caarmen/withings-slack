from typing import Any, Callable

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.localrepository.localfitbitrepository import (
    LocalFitbitRepository,
)
from slackhealthbot.domain.modelmappers.remoteservicetocore import oauth


class UpdateTokenUseCase(Callable):

    def __init__(
        self, request_context_fitbit_repository: Callable[[], LocalFitbitRepository]
    ):
        self.request_context_fitbit_repository = request_context_fitbit_repository

    async def __call__(self, token: dict[str, Any], **kwargs):
        repo: LocalFitbitRepository = self.request_context_fitbit_repository()
        oauth_fields: OAuthFields = oauth.remote_service_oauth_to_core_oauth(token)
        await repo.update_oauth_data(
            fitbit_userid=oauth_fields.oauth_userid,
            oauth_data=oauth_fields,
        )
