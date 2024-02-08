import dataclasses
import datetime

from sqlalchemy import and_, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.data.database import models


@dataclasses.dataclass
class UserIdentity:
    fitbit_userid: str
    slack_alias: str


@dataclasses.dataclass
class OAuthData:
    oauth_access_token: str
    oauth_refresh_token: str
    oauth_expiration_date: datetime.datetime


@dataclasses.dataclass
class User:
    identity: UserIdentity
    oauth_data: OAuthData


@dataclasses.dataclass
class Activity:
    log_id: int
    type_id: int
    total_minutes: int
    calories: int | None = None
    fat_burn_minutes: int | None = None
    cardio_minutes: int | None = None
    peak_minutes: int | None = None
    out_of_range_minutes: int | None = None


@dataclasses.dataclass
class Sleep:
    start_time: datetime.datetime
    end_time: datetime.datetime
    sleep_minutes: int
    wake_minutes: int


async def create_user(
    db: AsyncSession,
    slack_alias: str,
    fitbit_userid: str,
    oauth_data: OAuthData,
) -> User:
    user = (
        await db.scalars(
            statement=select(models.User).where(models.User.slack_alias == slack_alias)
        )
    ).one_or_none()
    if not user:
        user = models.User(slack_alias=slack_alias)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    fitbit_user = models.FitbitUser(
        user_id=user.id,
        oauth_userid=fitbit_userid,
        oauth_access_token=oauth_data.oauth_access_token,
        oauth_refresh_token=oauth_data.oauth_refresh_token,
        oauth_expiration_date=oauth_data.oauth_expiration_date,
    )
    db.add(fitbit_user)
    await db.commit()
    await db.refresh(fitbit_user)

    return User(
        identity=UserIdentity(
            fitbit_userid=fitbit_user.oauth_userid,
            slack_alias=slack_alias,
        ),
        oauth_data=OAuthData(
            oauth_access_token=fitbit_user.oauth_access_token,
            oauth_refresh_token=fitbit_user.oauth_refresh_token,
            oauth_expiration_date=fitbit_user.oauth_expiration_date.replace(
                tzinfo=datetime.timezone.utc
            ),
        ),
    )


async def get_user_identity_by_fitbit_userid(
    db: AsyncSession,
    fitbit_userid: str,
) -> UserIdentity | None:
    user: models.User = (
        await db.scalars(
            statement=select(models.User)
            .join(models.User.fitbit)
            .where(models.FitbitUser.oauth_userid == fitbit_userid)
        )
    ).one_or_none()
    return (
        UserIdentity(
            fitbit_userid=user.fitbit.oauth_userid,
            slack_alias=user.slack_alias,
        )
        if user
        else None
    )


async def get_all_user_identities(
    db: AsyncSession,
) -> list[UserIdentity]:
    users = await db.scalars(statement=select(models.User).join(models.User.fitbit))
    return [
        UserIdentity(fitbit_userid=x.fitbit.oauth_userid, slack_alias=x.slack_alias)
        for x in users
    ]


async def get_oauth_data_by_fitbit_userid(
    db: AsyncSession,
    fitbit_userid: str,
) -> OAuthData:
    fitbit_user: models.FitbitUser = (
        await db.scalars(
            statement=select(models.FitbitUser).where(
                models.FitbitUser.oauth_userid == fitbit_userid
            )
        )
    ).one()
    return OAuthData(
        oauth_access_token=fitbit_user.oauth_access_token,
        oauth_refresh_token=fitbit_user.oauth_refresh_token,
        oauth_expiration_date=fitbit_user.oauth_expiration_date.replace(
            tzinfo=datetime.timezone.utc
        ),
    )


async def get_user_by_fitbit_userid(
    db: AsyncSession,
    fitbit_userid: str,
) -> User:
    user: models.User = (
        await db.scalars(
            statement=select(models.User)
            .join(models.User.fitbit)
            .where(models.FitbitUser.oauth_userid == fitbit_userid)
        )
    ).one()
    return User(
        identity=UserIdentity(
            fitbit_userid=user.fitbit.oauth_userid,
            slack_alias=user.slack_alias,
        ),
        oauth_data=OAuthData(
            oauth_access_token=user.fitbit.oauth_access_token,
            oauth_refresh_token=user.fitbit.oauth_refresh_token,
            oauth_expiration_date=user.fitbit.oauth_expiration_date.replace(
                tzinfo=datetime.timezone.utc
            ),
        ),
    )


async def get_latest_activity_by_user_and_type(
    db: AsyncSession,
    fitbit_userid: str,
    type_id: int,
) -> Activity | None:
    db_activity: models.FitbitActivity = await db.scalar(
        statement=select(models.FitbitActivity)
        .join(
            models.FitbitUser,
            models.FitbitUser.id == models.FitbitActivity.fitbit_user_id,
        )
        .where(
            and_(
                models.FitbitUser.oauth_userid == fitbit_userid,
                models.FitbitActivity.type_id == type_id,
            )
        )
        .order_by(desc(models.FitbitActivity.updated_at))
        .limit(1)
    )
    return (
        Activity(
            log_id=db_activity.log_id,
            type_id=db_activity.type_id,
            total_minutes=db_activity.total_minutes,
            calories=db_activity.calories,
            fat_burn_minutes=db_activity.fat_burn_minutes,
            cardio_minutes=db_activity.cardio_minutes,
            peak_minutes=db_activity.peak_minutes,
            out_of_range_minutes=db_activity.out_of_range_minutes,
        )
        if db_activity
        else None
    )


async def get_activity_by_user_and_log_id(
    db: AsyncSession,
    fitbit_userid: str,
    log_id: int,
) -> Activity | None:
    db_activity: models.FitbitActivity = (
        await db.scalars(
            statement=select(models.FitbitActivity)
            .join(models.FitbitUser)
            .where(
                and_(
                    models.FitbitUser.oauth_userid == fitbit_userid,
                    models.FitbitActivity.log_id == log_id,
                )
            )
        )
    ).one_or_none()
    return (
        Activity(
            log_id=db_activity.log_id,
            type_id=db_activity.type_id,
            total_minutes=db_activity.total_minutes,
            calories=db_activity.calories,
            fat_burn_minutes=db_activity.fat_burn_minutes,
            cardio_minutes=db_activity.cardio_minutes,
            peak_minutes=db_activity.peak_minutes,
            out_of_range_minutes=db_activity.out_of_range_minutes,
        )
        if db_activity
        else None
    )


async def create_activity_for_user(
    db: AsyncSession,
    fitbit_userid: str,
    activity: Activity,
):
    user: models.FitbitUser = (
        await db.scalars(
            statement=select(models.FitbitUser).where(
                models.FitbitUser.oauth_userid == fitbit_userid
            )
        )
    ).one_or_none()
    fitbit_activity = models.FitbitActivity(
        log_id=activity.log_id,
        type_id=activity.type_id,
        total_minutes=activity.total_minutes,
        calories=activity.calories,
        fat_burn_minutes=activity.fat_burn_minutes,
        cardio_minutes=activity.cardio_minutes,
        peak_minutes=activity.peak_minutes,
        out_of_range_minutes=activity.out_of_range_minutes,
        fitbit_user_id=user.id,
    )
    db.add(fitbit_activity)
    await db.commit()


async def update_activity(
    db: AsyncSession,
    activity: Activity,
):
    await db.execute(
        statement=update(models.FitbitActivity)
        .where(models.FitbitActivity.log_id == activity.log_id)
        .values(
            type_id=activity.type_id,
            total_minutes=activity.total_minutes,
            calories=activity.calories,
            fat_burn_minutes=activity.fat_burn_minutes,
            cardio_minutes=activity.cardio_minutes,
            peak_minutes=activity.peak_minutes,
            out_of_range_minutes=activity.out_of_range_minutes,
        )
    )
    await db.commit()


async def update_sleep_for_user(
    db: AsyncSession,
    fitbit_userid: str,
    sleep: Sleep,
):
    await db.execute(
        statement=update(models.FitbitUser)
        .where(models.FitbitUser.oauth_userid == fitbit_userid)
        .values(
            last_sleep_start_time=sleep.start_time,
            last_sleep_end_time=sleep.end_time,
            last_sleep_sleep_minutes=sleep.sleep_minutes,
            last_sleep_wake_minutes=sleep.wake_minutes,
        )
    )


async def get_sleep_by_fitbit_userid(
    db: AsyncSession,
    fitbit_userid: str,
) -> Sleep | None:
    fitbit_user: models.FitbitUser = (
        await db.scalars(
            statement=select(models.FitbitUser).where(
                models.FitbitUser.oauth_userid == fitbit_userid
            )
        )
    ).one()
    if not fitbit_user or not fitbit_user.last_sleep_end_time:
        return None
    return Sleep(
        start_time=fitbit_user.last_sleep_start_time,
        end_time=fitbit_user.last_sleep_end_time,
        sleep_minutes=fitbit_user.last_sleep_sleep_minutes,
        wake_minutes=fitbit_user.last_sleep_wake_minutes,
    )


async def update_oauth_data(
    db: AsyncSession,
    fitbit_userid: str,
    oauth_data: OAuthData,
):
    await db.execute(
        statement=update(models.FitbitUser)
        .where(models.FitbitUser.oauth_userid == fitbit_userid)
        .values(
            oauth_access_token=oauth_data.oauth_access_token,
            oauth_refresh_token=oauth_data.oauth_refresh_token,
            oauth_expiration_date=oauth_data.oauth_expiration_date,
        )
    )
    await db.commit()
