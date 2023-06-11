import pytest
from pytest_factoryboy import register

from slackhealthbot.database.models import Base
from tests.factories.factories import (
    FitbitUserFactory,
    UserFactory,
    WithingsUserFactory,
)


@pytest.fixture(scope="function")
def sqlalchemy_declarative_base():
    return Base


@pytest.fixture(scope="function", autouse=True)
def setup_factories(mocked_session):
    for factory in [UserFactory, WithingsUserFactory, FitbitUserFactory]:
        factory._meta.sqlalchemy_session = mocked_session
        factory._meta.sqlalchemy_session_persistence = "commit"


for factory in [UserFactory, WithingsUserFactory, FitbitUserFactory]:
    register(factory)
