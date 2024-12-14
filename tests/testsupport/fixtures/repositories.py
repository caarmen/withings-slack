import pytest
from sqlalchemy.ext.asyncio import AsyncSession

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
from slackhealthbot.remoteservices.repositories.webapifitbitrepository import (
    WebApiFitbitRepository,
)
from slackhealthbot.remoteservices.repositories.webapiwithingsrepository import (
    WebApiWithingsRepository,
)


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
