from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.database import crud
from slackhealthbot.database.models import (
    FitbitLatestActivity,
    FitbitUser,
    User,
    WithingsUser,
)
from tests.factories.factories import (
    FitbitLatestActivityFactory,
    FitbitUserFactory,
    UserFactory,
    WithingsUserFactory,
)


@pytest.mark.asyncio
async def test_user_factory(
    user_factory: UserFactory,
    mocked_async_session,
):
    user: User = user_factory()
    assert isinstance(user.slack_alias, str)
    assert isinstance(user.id, int)
    assert isinstance(user.withings, WithingsUser)
    assert isinstance(user.fitbit, FitbitUser)
    db_user = await crud.get_user(mocked_async_session, slack_alias=user.slack_alias)
    assert user.id == db_user.id
    assert user.slack_alias == db_user.slack_alias
    assert user.withings.id == db_user.withings.id
    assert user.fitbit.id == db_user.fitbit.id


@pytest.mark.asyncio
async def test_withings_user_factory(
    user_factory: UserFactory,
    withings_user_factory: WithingsUserFactory,
    mocked_async_session,
):
    user: User = user_factory(withings=None)
    withings_user: WithingsUser = withings_user_factory(user_id=user.id)
    assert isinstance(withings_user.oauth_access_token, str)
    assert isinstance(withings_user.oauth_refresh_token, str)
    assert isinstance(withings_user.oauth_userid, str)
    assert isinstance(withings_user.oauth_expiration_date, datetime)
    assert isinstance(withings_user.last_weight, float)
    assert isinstance(user, User)

    db_user = await crud.get_user(
        mocked_async_session, withings_oauth_userid=withings_user.oauth_userid
    )
    db_withings_user = db_user.withings
    assert db_withings_user.oauth_access_token == withings_user.oauth_access_token
    assert db_withings_user.oauth_refresh_token == withings_user.oauth_refresh_token
    assert db_withings_user.oauth_userid == withings_user.oauth_userid
    assert db_withings_user.oauth_expiration_date == withings_user.oauth_expiration_date
    assert db_withings_user.last_weight == withings_user.last_weight
    assert db_withings_user.user.id == user.id


@pytest.mark.asyncio
async def test_fitbit_user_factory(
    user_factory: UserFactory,
    fitbit_user_factory: FitbitUserFactory,
    mocked_async_session: AsyncSession,
):
    user: User = user_factory(fitbit=None)
    fitbit_user: FitbitUser = fitbit_user_factory(user_id=user.id)
    assert isinstance(fitbit_user.oauth_access_token, str)
    assert isinstance(fitbit_user.oauth_refresh_token, str)
    assert isinstance(fitbit_user.oauth_userid, str)
    assert isinstance(fitbit_user.oauth_expiration_date, datetime)
    assert isinstance(user, User)

    db_user = await crud.get_user(
        mocked_async_session, fitbit_oauth_userid=fitbit_user.oauth_userid
    )
    db_fitbit_user = db_user.fitbit
    assert db_fitbit_user.oauth_access_token == fitbit_user.oauth_access_token
    assert db_fitbit_user.oauth_refresh_token == fitbit_user.oauth_refresh_token
    assert db_fitbit_user.oauth_userid == fitbit_user.oauth_userid
    assert db_fitbit_user.oauth_expiration_date == fitbit_user.oauth_expiration_date
    assert db_fitbit_user.user.id == user.id


@pytest.mark.asyncio
async def test_fitbit_latest_activity_factory(
    user_factory: UserFactory,
    fitbit_user_factory: FitbitUserFactory,
    fitbit_latest_activity_factory: FitbitLatestActivityFactory,
    mocked_async_session: AsyncSession,
):
    user: User = user_factory(fitbit=None)
    fitbit_user: FitbitUser = fitbit_user_factory(user_id=user.id)
    fitbit_latest_activity: FitbitLatestActivity = fitbit_latest_activity_factory(
        fitbit_user_id=fitbit_user.id
    )
    db_user = await crud.get_user(
        mocked_async_session, fitbit_oauth_userid=fitbit_user.oauth_userid
    )
    db_fitbit_latest_activities: list[
        FitbitLatestActivity
    ] = await db_user.fitbit.awaitable_attrs.latest_activities
    assert len(db_fitbit_latest_activities) == 1
    db_fitbit_latest_activity = db_fitbit_latest_activities[0]
    assert db_fitbit_latest_activity.log_id == fitbit_latest_activity.log_id
    assert db_fitbit_latest_activity.type_id == fitbit_latest_activity.type_id
    assert (
        db_fitbit_latest_activity.total_minutes == fitbit_latest_activity.total_minutes
    )
    assert db_fitbit_latest_activity.calories == fitbit_latest_activity.calories
    assert (
        db_fitbit_latest_activity.fat_burn_minutes
        == fitbit_latest_activity.fat_burn_minutes
    )
    assert (
        db_fitbit_latest_activity.cardio_minutes
        == fitbit_latest_activity.cardio_minutes
    )
    assert db_fitbit_latest_activity.peak_minutes == fitbit_latest_activity.peak_minutes
    assert (
        db_fitbit_latest_activity.out_of_range_minutes
        == fitbit_latest_activity.out_of_range_minutes
    )
