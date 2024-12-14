import pytest
from fastapi.testclient import TestClient

from slackhealthbot.main import app
from slackhealthbot.routers.dependencies import get_db
from slackhealthbot.settings import Settings


@pytest.fixture
def client(mocked_async_session) -> TestClient:
    app.dependency_overrides[get_db] = lambda: mocked_async_session
    return TestClient(app)


@pytest.fixture(autouse=True)
def settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv(
        "SHB_CUSTOM_CONFIG_PATH", "tests/testsupport/config/app-test.yaml"
    )
    return app.container.settings.provided()
