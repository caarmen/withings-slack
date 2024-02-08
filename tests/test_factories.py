from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.data.database.models import (
    FitbitActivity,
    FitbitUser,
    User,
    WithingsUser,
)
from slackhealthbot.data.repositories import fitbitrepository, withingsrepository
from tests.factories.factories import (
    FitbitActivityFactory,
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
    db_user: User = (
        await mocked_async_session.scalars(
            statement=select(User).where(User.slack_alias == user.slack_alias)
        )
    ).one()
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

    repo_user = await withingsrepository.get_user_by_withings_userid(
        mocked_async_session, withings_userid=withings_user.oauth_userid
    )
    assert repo_user.identity.withings_userid == withings_user.oauth_userid
    assert repo_user.oauth_data.oauth_access_token == withings_user.oauth_access_token
    assert repo_user.oauth_data.oauth_refresh_token == withings_user.oauth_refresh_token
    assert (
        repo_user.oauth_data.oauth_expiration_date
        == withings_user.oauth_expiration_date.replace(tzinfo=timezone.utc)
    )
    assert repo_user.fitness_data.last_weight_kg == withings_user.last_weight


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

    repo_user = await fitbitrepository.get_user_by_fitbit_userid(
        mocked_async_session, fitbit_userid=fitbit_user.oauth_userid
    )
    assert repo_user.oauth_data.oauth_access_token == fitbit_user.oauth_access_token
    assert repo_user.oauth_data.oauth_refresh_token == fitbit_user.oauth_refresh_token
    assert repo_user.identity.fitbit_userid == fitbit_user.oauth_userid
    assert (
        repo_user.oauth_data.oauth_expiration_date
        == fitbit_user.oauth_expiration_date.replace(tzinfo=timezone.utc)
    )


@pytest.mark.asyncio
async def test_fitbit_activity_factory(
    user_factory: UserFactory,
    fitbit_user_factory: FitbitUserFactory,
    fitbit_activity_factory: FitbitActivityFactory,
    mocked_async_session: AsyncSession,
):
    user: User = user_factory(fitbit=None)
    fitbit_user: FitbitUser = fitbit_user_factory(user_id=user.id)
    fitbit_activity: FitbitActivity = fitbit_activity_factory(
        fitbit_user_id=fitbit_user.id
    )
    repo_activity: fitbitrepository.Activity = (
        await fitbitrepository.get_latest_activity_by_user_and_type(
            mocked_async_session,
            fitbit_userid=fitbit_user.oauth_userid,
            type_id=fitbit_activity.type_id,
        )
    )
    assert repo_activity.log_id == fitbit_activity.log_id
    assert repo_activity.type_id == fitbit_activity.type_id
    assert repo_activity.total_minutes == fitbit_activity.total_minutes
    assert repo_activity.calories == fitbit_activity.calories
    assert repo_activity.fat_burn_minutes == fitbit_activity.fat_burn_minutes
    assert repo_activity.cardio_minutes == fitbit_activity.cardio_minutes
    assert repo_activity.peak_minutes == fitbit_activity.peak_minutes
    assert repo_activity.out_of_range_minutes == fitbit_activity.out_of_range_minutes
