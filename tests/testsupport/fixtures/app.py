import pytest
from fastapi.testclient import TestClient

from slackhealthbot.main import app
from slackhealthbot.routers.dependencies import get_db


@pytest.fixture
def client(mocked_async_session) -> TestClient:
    app.dependency_overrides[get_db] = lambda: mocked_async_session
    return TestClient(app)
