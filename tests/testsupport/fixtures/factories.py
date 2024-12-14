import pytest
from pytest_factoryboy import register

from tests.testsupport.factories.factories import (
    FitbitActivityFactory,
    FitbitUserFactory,
    UserFactory,
    WithingsUserFactory,
)


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
