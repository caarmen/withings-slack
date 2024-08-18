from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from pytest_factoryboy import register
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from alembic import command
from alembic.config import Config
from slackhealthbot.data.database import connection as db_connection
from slackhealthbot.data.database.models import Base
from slackhealthbot.data.repositories.sqlalchemyfitbitrepository import (
    SQLAlchemyFitbitRepository,
)
from slackhealthbot.data.repositories.sqlalchemywithingsrepository import (
    SQLAlchemyWithingsRepository,
)
from slackhealthbot.domain.localrepository.localfitbitrepository import (
    LocalFitbitRepository,
)
from slackhealthbot.domain.localrepository.localwithingsrepository import (
    LocalWithingsRepository,
)
from slackhealthbot.domain.remoterepository.remotefitbitrepository import (
    RemoteFitbitRepository,
)
from slackhealthbot.domain.remoterepository.remotewithingsrepository import (
    RemoteWithingsRepository,
)
from slackhealthbot.main import app
from slackhealthbot.remoteservices.repositories.webapifitbitrepository import (
    WebApiFitbitRepository,
)
from slackhealthbot.remoteservices.repositories.webapiwithingsrepository import (
    WebApiWithingsRepository,
)
from slackhealthbot.routers.dependencies import get_db
from tests.testsupport.factories.factories import (
    FitbitActivityFactory,
    FitbitUserFactory,
    UserFactory,
    WithingsUserFactory,
)


@pytest.fixture
def sqlalchemy_declarative_base():
    return Base


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    return str(tmp_path / "database.db")


@pytest.fixture
def async_connection_url(db_path):
    return f"sqlite+aiosqlite:///{db_path}"


@pytest.fixture
def connection_url(db_path):
    return f"sqlite:///{db_path}"


@pytest.fixture()
def apply_alembic_migration(
    async_connection_url: str,
    monkeypatch: pytest.MonkeyPatch,
):
    with monkeypatch.context() as mp:
        mp.setattr(db_connection, "connection_url", async_connection_url)
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")


@pytest.fixture(autouse=True)
def setup_db(apply_alembic_migration, connection):
    # This fixture ensures that the alembic migration is applied
    # before the connection fixture is used.
    pass


@pytest_asyncio.fixture
async def mocked_async_session(async_connection_url: str):
    engine = create_async_engine(async_connection_url)
    session: AsyncSession = async_sessionmaker(bind=engine)()
    yield session
    await session.close()


@pytest.fixture
def local_withings_repository(
    mocked_async_session: AsyncSession,
) -> LocalWithingsRepository:
    return SQLAlchemyWithingsRepository(db=mocked_async_session)


@pytest.fixture
def remote_withings_repository() -> RemoteWithingsRepository:
    return WebApiWithingsRepository()


@pytest.fixture
def local_fitbit_repository(
    mocked_async_session: AsyncSession,
) -> LocalFitbitRepository:
    return SQLAlchemyFitbitRepository(db=mocked_async_session)


@pytest.fixture
def remote_fitbit_repository() -> RemoteFitbitRepository:
    return WebApiFitbitRepository()


@pytest.fixture
def fitbit_repositories(
    local_fitbit_repository: LocalFitbitRepository,
    remote_fitbit_repository: RemoteFitbitRepository,
) -> tuple[LocalFitbitRepository, RemoteFitbitRepository]:
    return local_fitbit_repository, remote_fitbit_repository


@pytest.fixture
def client(mocked_async_session) -> TestClient:
    app.dependency_overrides[get_db] = lambda: mocked_async_session
    return TestClient(app)


@pytest.fixture
def withings_factories(
    user_factory: UserFactory,
    withings_user_factory: WithingsUserFactory,
) -> tuple[UserFactory, WithingsUserFactory]:
    return user_factory, withings_user_factory


@pytest.fixture
def fitbit_factories(
    user_factory: UserFactory,
    fitbit_user_factory: FitbitUserFactory,
    fitbit_activity_factory: FitbitActivityFactory,
) -> tuple[UserFactory, FitbitUserFactory, FitbitActivityFactory]:
    return user_factory, fitbit_user_factory, fitbit_activity_factory


@pytest.fixture(scope="function", autouse=True)
def setup_factories(mocked_session):
    for factory in [
        UserFactory,
        WithingsUserFactory,
        FitbitUserFactory,
        FitbitActivityFactory,
    ]:
        # The _meta attribute is documented:
        # https://factoryboy.readthedocs.io/en/stable/reference.html#factory.Factory._meta
        # noinspection PyProtectedMember
        factory._meta.sqlalchemy_session = mocked_session
        # noinspection PyProtectedMember
        factory._meta.sqlalchemy_session_persistence = "commit"


for factory in [
    UserFactory,
    WithingsUserFactory,
    FitbitUserFactory,
    FitbitActivityFactory,
]:
    register(factory)
