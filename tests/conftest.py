import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from pytest_factoryboy import register
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm.session import Session

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
from slackhealthbot.main import app
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
def withings_repository(
    mocked_async_session: AsyncSession,
) -> LocalWithingsRepository:
    return SQLAlchemyWithingsRepository(db=mocked_async_session)


@pytest.fixture
def fitbit_repository(
    mocked_async_session: AsyncSession,
) -> LocalFitbitRepository:
    return SQLAlchemyFitbitRepository(db=mocked_async_session)


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
