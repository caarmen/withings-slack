import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from pytest_factoryboy import register
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm.session import Session

from slackhealthbot.database.models import Base
from slackhealthbot.main import app, get_db
from tests.factories.factories import (
    FitbitLatestActivityFactory,
    FitbitUserFactory,
    UserFactory,
    WithingsUserFactory,
)


@pytest.fixture
def sqlalchemy_declarative_base():
    return Base


@pytest.fixture
def connection_url(tmp_path):
    return f"sqlite:///{tmp_path / 'database.db'}"


@pytest_asyncio.fixture
async def mocked_async_session(mocked_session: Session):
    connection_url = f"sqlite+aiosqlite:///{mocked_session.bind.engine.url.database}"
    engine = create_async_engine(connection_url)
    session: AsyncSession = async_sessionmaker(bind=engine)()
    yield session
    await session.close()


@pytest.fixture
def client(mocked_async_session) -> TestClient:
    app.dependency_overrides[get_db] = lambda: mocked_async_session
    return TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_factories(mocked_session):
    for factory in [
        UserFactory,
        WithingsUserFactory,
        FitbitUserFactory,
        FitbitLatestActivityFactory,
    ]:
        factory._meta.sqlalchemy_session = mocked_session
        factory._meta.sqlalchemy_session_persistence = "commit"


for factory in [
    UserFactory,
    WithingsUserFactory,
    FitbitUserFactory,
    FitbitLatestActivityFactory,
]:
    register(factory)
