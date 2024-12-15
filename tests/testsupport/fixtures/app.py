import pytest
from fastapi.testclient import TestClient

from slackhealthbot.main import app
from slackhealthbot.routers.dependencies import get_db
from slackhealthbot.settings import Settings


@pytest.fixture
def client(mocked_async_session) -> TestClient:
    app.dependency_overrides[get_db] = lambda: mocked_async_session
    return TestClient(app)


@pytest.fixture
def settings() -> Settings:
    return app.container.settings.provided()
