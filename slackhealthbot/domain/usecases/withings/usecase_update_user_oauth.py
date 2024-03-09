from typing import Any, Callable

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.domain.modelmappers.remoteservicetocore import oauth
from slackhealthbot.domain.repository.withingsrepository import WithingsRepository


class UpdateTokenUseCase(Callable):

    def __init__(
        self, request_context_withings_repository: Callable[[], WithingsRepository]
    ):
        self.request_context_withings_repository = request_context_withings_repository

    async def __call__(self, token: dict[str, Any], **kwargs):
        repo: WithingsRepository = self.request_context_withings_repository()
        oauth_fields: OAuthFields = oauth.remote_service_oauth_to_core_oauth(token)
        await repo.update_oauth_data(
            withings_userid=oauth_fields.oauth_userid,
            oauth_data=oauth_fields,
        )
