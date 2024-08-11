import datetime

import pytest

from slackhealthbot.data.database import models
from slackhealthbot.domain.localrepository.localfitbitrepository import (
    LocalFitbitRepository,
)
from slackhealthbot.domain.models.activity import (
    ActivityZone,
    ActivityZoneMinutes,
    DailyActivityStats,
    TopActivityStats,
)
from tests.testsupport.factories.factories import (
    FitbitActivityFactory,
    FitbitUserFactory,
    UserFactory,
)


@pytest.mark.asyncio
async def test_top_activities(
    local_fitbit_repository: LocalFitbitRepository,
    fitbit_factories: tuple[UserFactory, FitbitUserFactory, FitbitActivityFactory],
):
    user_factory, _, fitbit_activity_factory = fitbit_factories
    activity_type = 111
    user: models.User = user_factory.create()
    other_user: models.User = user_factory.create()

    recent_date = datetime.datetime(2024, 1, 2, 23, 44, 55)
    old_date = datetime.datetime(2023, 3, 4, 15, 44, 33)

    # Our user, our activity, all-time top record for calories and distance
    all_time_top_calories_and_distance_activity: models.FitbitActivity = (
        fitbit_activity_factory.create(
            fitbit_user_id=user.fitbit.id,
            type_id=activity_type,
            calories=600,
            distance_km=3.2,
            total_minutes=18,
            fat_burn_minutes=17,
            cardio_minutes=16,
            peak_minutes=15,
            updated_at=old_date,
        )
    )

    # Our user, our activity, recent top record for calories and distance
    recent_top_calories_and_distance_activity: models.FitbitActivity = (
        fitbit_activity_factory.create(
            fitbit_user_id=user.fitbit.id,
            type_id=activity_type,
            calories=599,
            distance_km=3.1,
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
            distance_km=2.5,
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
        distance_km=2.5,
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
        distance_km=2.8,
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
        distance_km=10.2,
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
        distance_km=8.3,
        total_minutes=98,
        fat_burn_minutes=97,
        cardio_minutes=96,
        peak_minutes=95,
        updated_at=recent_date,
    )

    all_time_top_activity_stats: TopActivityStats = (
        await local_fitbit_repository.get_top_activity_stats_by_user_and_activity_type(
            fitbit_userid=user.fitbit.oauth_userid,
            type_id=activity_type,
        )
    )
    assert all_time_top_activity_stats == TopActivityStats(
        top_calories=all_time_top_calories_and_distance_activity.calories,
        top_distance_km=all_time_top_calories_and_distance_activity.distance_km,
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
        await local_fitbit_repository.get_top_activity_stats_by_user_and_activity_type(
            fitbit_userid=user.fitbit.oauth_userid,
            type_id=activity_type,
            since=recent_date - datetime.timedelta(days=1),
        )
    )
    assert recent_top_activity_stats == TopActivityStats(
        top_calories=recent_top_calories_and_distance_activity.calories,
        top_distance_km=recent_top_calories_and_distance_activity.distance_km,
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
    local_fitbit_repository: LocalFitbitRepository,
    fitbit_factories: tuple[UserFactory, FitbitUserFactory, FitbitActivityFactory],
):
    user_factory, _, _ = fitbit_factories
    activity_type = 111
    user: models.User = user_factory.create()
    recent_date = datetime.datetime(2024, 1, 2, 23, 44, 55)

    all_time_top_activity_stats: TopActivityStats = (
        await local_fitbit_repository.get_top_activity_stats_by_user_and_activity_type(
            fitbit_userid=user.fitbit.oauth_userid,
            type_id=activity_type,
        )
    )
    assert all_time_top_activity_stats == TopActivityStats(
        top_calories=None,
        top_distance_km=None,
        top_total_minutes=None,
        top_zone_minutes=[],
    )

    recent_top_activity_stats: TopActivityStats = (
        await local_fitbit_repository.get_top_activity_stats_by_user_and_activity_type(
            fitbit_userid=user.fitbit.oauth_userid,
            type_id=activity_type,
            since=recent_date - datetime.timedelta(days=1),
        )
    )
    assert recent_top_activity_stats == TopActivityStats(
        top_calories=None,
        top_distance_km=None,
        top_total_minutes=None,
        top_zone_minutes=[],
    )


@pytest.mark.asyncio
async def test_daily_activities_one_entry(
    local_fitbit_repository: LocalFitbitRepository,
    fitbit_factories: tuple[UserFactory, FitbitUserFactory, FitbitActivityFactory],
):
    """
    Given multiple activities of one given type for a user on one day
    When we request the daily activities for that day
    Then we get the expected aggregation counts.
    """
    user_factory, _, fitbit_activity_factory = fitbit_factories
    user: models.User = user_factory.create(slack_alias="jondoe")
    fitbit_activity_factory.create(
        fitbit_user_id=user.fitbit.id,
        type_id=1234,
        calories=400,
        distance_km=2.8,
        total_minutes=20,
        fat_burn_minutes=19,
        cardio_minutes=18,
        peak_minutes=17,
        out_of_range_minutes=None,
        updated_at=datetime.datetime(2024, 1, 2, 23, 44, 55),
    )
    fitbit_activity_factory.create(
        fitbit_user_id=user.fitbit.id,
        type_id=1234,
        calories=500,
        distance_km=2.6,
        total_minutes=10,
        fat_burn_minutes=18,
        cardio_minutes=17,
        peak_minutes=None,
        out_of_range_minutes=None,
        updated_at=datetime.datetime(2024, 1, 2, 23, 44, 55),
    )

    actual_daily_activity_stats: list[DailyActivityStats] = (
        await local_fitbit_repository.get_daily_activities_by_type(
            type_ids={1234},
            when=datetime.date(2024, 1, 2),
        )
    )
    expected_daily_activity_stats = [
        DailyActivityStats(
            fitbit_userid=user.fitbit.oauth_userid,
            slack_alias="jondoe",
            type_id=1234,
            count_activities=2,
            sum_calories=900,
            sum_distance_km=pytest.approx(5.4),
            sum_total_minutes=30,
            sum_fat_burn_minutes=37,
            sum_cardio_minutes=35,
            sum_peak_minutes=17,
            sum_out_of_range_minutes=None,
        )
    ]
    assert actual_daily_activity_stats == expected_daily_activity_stats


@pytest.mark.asyncio
async def test_daily_activities_multiple_entries(
    local_fitbit_repository: LocalFitbitRepository,
    fitbit_factories: tuple[UserFactory, FitbitUserFactory, FitbitActivityFactory],
):
    """
    Given activities for multiple users and types for a given date
    When we request the daily activities for that day
    Then we get the expected aggregation counts.
    """
    user_factory, _, fitbit_activity_factory = fitbit_factories
    user1: models.User = user_factory.create(slack_alias="user1")
    user2: models.User = user_factory.create(slack_alias="user2")

    # Matching entries:
    # User 1:
    fitbit_activity_factory.create(
        fitbit_user_id=user1.fitbit.id,
        type_id=1235,
        updated_at=datetime.datetime(2024, 1, 2, 3, 3, 4),
    )
    fitbit_activity_factory.create(
        fitbit_user_id=user1.fitbit.id,
        type_id=1235,
        updated_at=datetime.datetime(2024, 1, 2, 4, 3, 4),
    )
    fitbit_activity_factory.create(
        fitbit_user_id=user1.fitbit.id,
        type_id=1234,
        updated_at=datetime.datetime(2024, 1, 2, 5, 3, 4),
    )
    # User 2:
    fitbit_activity_factory.create(
        fitbit_user_id=user2.fitbit.id,
        type_id=1234,
        updated_at=datetime.datetime(2024, 1, 2, 5, 3, 4),
    )

    # Not matching entries:
    # User 1:
    fitbit_activity_factory.create(
        fitbit_user_id=user1.fitbit.id,
        type_id=1234,
        updated_at=datetime.datetime(2024, 1, 4, 1, 3, 3),
    )
    fitbit_activity_factory.create(
        fitbit_user_id=user1.fitbit.id,
        type_id=1235,
        updated_at=datetime.datetime(2024, 1, 4, 1, 2, 3),
    )
    # User 2:
    fitbit_activity_factory.create(
        fitbit_user_id=user2.fitbit.id,
        type_id=1235,
        updated_at=datetime.datetime(2023, 12, 4, 1, 2, 3),
    )

    # Get the list of daily activity stats for all users and activity types
    list_daily_activity_stats: list[DailyActivityStats] = (
        await local_fitbit_repository.get_daily_activities_by_type(
            type_ids={1234, 1235},
            when=datetime.date(2024, 1, 2),
        )
    )
    assert len(list_daily_activity_stats) == 3  # noqa: PLR2004

    actual_counts = {
        (
            x.slack_alias,
            x.type_id,
            x.count_activities,
        )
        for x in list_daily_activity_stats
    }
    expected_counts = {
        (
            "user1",
            1234,
            1,
        ),
        (
            "user1",
            1235,
            2,
        ),
        (
            "user2",
            1234,
            1,
        ),
    }
    assert actual_counts == expected_counts
