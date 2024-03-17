from slackhealthbot.domain.remoterepository.remoteslackrepository import (
    RemoteSlackRepository,
)
from slackhealthbot.remoteservices.api.slack import messageapi


class WebhookSlackRepository(RemoteSlackRepository):
    async def post_message(self, message: str):
        await messageapi.post_message(message)
