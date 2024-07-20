from abc import ABC, abstractmethod


class RemoteSlackRepository(ABC):
    @abstractmethod
    async def post_message(self, message: str):
        pass
