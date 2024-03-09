import datetime

import pytest

from slackhealthbot.data.database import models
from slackhealthbot.domain.models.activity import (
    ActivityZone,
    ActivityZoneMinutes,
    TopActivityStats,
)
from slackhealthbot.domain.repository.fitbitrepository import FitbitRepository
from tests.testsupport.factories.factories import (
    FitbitActivityFactory,
    FitbitUserFactory,
    UserFactory,
)


@pytest.mark.asyncio
async def test_top_activities(
    fitbit_repository: FitbitRepository,
    fitbit_factories: tuple[UserFactory, FitbitUserFactory, FitbitActivityFactory],
):
    user_factory, _, fitbit_activity_factory = fitbit_factories
    activity_type = 111
    user: models.User = user_factory.create()
    other_user: models.User = user_factory.create()

    recent_date = datetime.datetime(2024, 1, 2, 23, 44, 55)
    old_date = datetime.datetime(2023, 3, 4, 15, 44, 33)

    # Our user, our activity, all-time top record for calories
    all_time_top_calories_activity: models.FitbitActivity = (
        fitbit_activity_factory.create(
            fitbit_user_id=user.fitbit.id,
            type_id=activity_type,
            calories=600,
            total_minutes=18,
            fat_burn_minutes=17,
            cardio_minutes=16,
            peak_minutes=15,
            updated_at=old_date,
        )
    )

    # Our user, our activity, recent top record for calories
    recent_top_calories_activity: models.FitbitActivity = (
        fitbit_activity_factory.create(
            fitbit_user_id=user.fitbit.id,
            type_id=activity_type,
            calories=599,
            total_minutes=18,
            fat_burn_minutes=17,
            cardio_minutes=16,
            peak_minutes=15,
            updated_at=recent_date,
        )
    )

    # Our user, our activity, all-time top record for the different minutes attributes
    all_time_top_minutes_activity: models.FitbitActivity = (
        fitbit_activity_factory.create(
            fitbit_user_id=user.fitbit.id,
            type_id=activity_type,
            calories=333,
            total_minutes=30,
            fat_burn_minutes=29,
            cardio_minutes=28,
            peak_minutes=27,
            updated_at=old_date,
        )
    )

    # Our user, our activity, recent top record for the different minutes attributes
    recent_top_minutes_activity: models.FitbitActivity = fitbit_activity_factory.create(
        fitbit_user_id=user.fitbit.id,
        type_id=activity_type,
        calories=333,
        total_minutes=29,
        fat_burn_minutes=28,
        cardio_minutes=27,
        peak_minutes=26,
        updated_at=recent_date,
    )

    # Our user, but not top stats
    fitbit_activity_factory.create(
        fitbit_user_id=user.fitbit.id,
        type_id=activity_type,
        calories=400,
        total_minutes=20,
        fat_burn_minutes=19,
        cardio_minutes=18,
        peak_minutes=17,
        updated_at=recent_date,
    )

    # Another user with higher stats
    fitbit_activity_factory.create(
        fitbit_user_id=other_user.fitbit.id,
        type_id=activity_type,
        calories=800,
        total_minutes=69,
        fat_burn_minutes=68,
        cardio_minutes=67,
        peak_minutes=66,
        updated_at=recent_date,
    )

    # Our user, with higher stats for another activity type
    fitbit_activity_factory.create(
        fitbit_user_id=user.fitbit.id,
        type_id=999,
        calories=900,
        total_minutes=98,
        fat_burn_minutes=97,
        cardio_minutes=96,
        peak_minutes=95,
        updated_at=recent_date,
    )

    all_time_top_activity_stats: TopActivityStats = (
        await fitbit_repository.get_top_activity_stats_by_user_and_activity_type(
            fitbit_userid=user.fitbit.oauth_userid,
            type_id=activity_type,
        )
    )
    assert all_time_top_activity_stats == TopActivityStats(
        top_calories=all_time_top_calories_activity.calories,
        top_total_minutes=all_time_top_minutes_activity.total_minutes,
        top_zone_minutes=[
            ActivityZoneMinutes(
                zone=ActivityZone.PEAK,
                minutes=all_time_top_minutes_activity.peak_minutes,
            ),
            ActivityZoneMinutes(
                zone=ActivityZone.CARDIO,
                minutes=all_time_top_minutes_activity.cardio_minutes,
            ),
            ActivityZoneMinutes(
                zone=ActivityZone.FAT_BURN,
                minutes=all_time_top_minutes_activity.fat_burn_minutes,
            ),
        ],
    )

    recent_top_activity_stats: TopActivityStats = (
        await fitbit_repository.get_top_activity_stats_by_user_and_activity_type(
            fitbit_userid=user.fitbit.oauth_userid,
            type_id=activity_type,
            since=recent_date - datetime.timedelta(days=1),
        )
    )
    assert recent_top_activity_stats == TopActivityStats(
        top_calories=recent_top_calories_activity.calories,
        top_total_minutes=recent_top_minutes_activity.total_minutes,
        top_zone_minutes=[
            ActivityZoneMinutes(
                zone=ActivityZone.PEAK,
                minutes=recent_top_minutes_activity.peak_minutes,
            ),
            ActivityZoneMinutes(
                zone=ActivityZone.CARDIO,
                minutes=recent_top_minutes_activity.cardio_minutes,
            ),
            ActivityZoneMinutes(
                zone=ActivityZone.FAT_BURN,
                minutes=recent_top_minutes_activity.fat_burn_minutes,
            ),
        ],
    )


@pytest.mark.asyncio
async def test_top_activities_no_history(
    fitbit_repository: FitbitRepository,
    fitbit_factories: tuple[UserFactory, FitbitUserFactory, FitbitActivityFactory],
):
    user_factory, _, _ = fitbit_factories
    activity_type = 111
    user: models.User = user_factory.create()
    recent_date = datetime.datetime(2024, 1, 2, 23, 44, 55)

    all_time_top_activity_stats: TopActivityStats = (
        await fitbit_repository.get_top_activity_stats_by_user_and_activity_type(
            fitbit_userid=user.fitbit.oauth_userid,
            type_id=activity_type,
        )
    )
    assert all_time_top_activity_stats == TopActivityStats(
        top_calories=None,
        top_total_minutes=None,
        top_zone_minutes=[],
    )

    recent_top_activity_stats: TopActivityStats = (
        await fitbit_repository.get_top_activity_stats_by_user_and_activity_type(
            fitbit_userid=user.fitbit.oauth_userid,
            type_id=activity_type,
            since=recent_date - datetime.timedelta(days=1),
        )
    )
    assert recent_top_activity_stats == TopActivityStats(
        top_calories=None,
        top_total_minutes=None,
        top_zone_minutes=[],
    )
