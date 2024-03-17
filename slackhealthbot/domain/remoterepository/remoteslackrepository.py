from abc import ABC


class RemoteSlackRepository(ABC):
    async def post_message(self, message: str):
        pass
