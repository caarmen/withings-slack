import dataclasses
import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.data.database import models


@dataclasses.dataclass
class UserIdentity:
    withings_userid: str
    slack_alias: str


@dataclasses.dataclass
class OAuthData:
    oauth_access_token: str
    oauth_refresh_token: str
    oauth_expiration_date: datetime.datetime


@dataclasses.dataclass
class FitnessData:
    last_weight_kg: float | None = None


@dataclasses.dataclass
class User:
    identity: UserIdentity
    oauth_data: OAuthData
    fitness_data: FitnessData


async def create_user(
    db: AsyncSession,
    slack_alias: str,
    withings_userid: str,
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

    withings_user = models.WithingsUser(
        user_id=user.id,
        oauth_userid=withings_userid,
        oauth_access_token=oauth_data.oauth_access_token,
        oauth_refresh_token=oauth_data.oauth_refresh_token,
        oauth_expiration_date=oauth_data.oauth_expiration_date,
    )
    db.add(withings_user)
    await db.commit()
    await db.refresh(withings_user)

    return User(
        identity=UserIdentity(
            withings_userid=withings_user,
            slack_alias=slack_alias,
        ),
        oauth_data=OAuthData(
            oauth_access_token=withings_user.oauth_access_token,
            oauth_refresh_token=withings_user.oauth_refresh_token,
            oauth_expiration_date=withings_user.oauth_expiration_date.replace(
                tzinfo=datetime.timezone.utc
            ),
        ),
        fitness_data=FitnessData(),
    )


async def get_user_identity_by_withings_userid(
    db: AsyncSession,
    withings_userid: str,
) -> UserIdentity | None:
    user: models.User = (
        await db.scalars(
            statement=select(models.User)
            .join(models.User.withings)
            .where(models.WithingsUser.oauth_userid == withings_userid)
        )
    ).one_or_none()
    return (
        UserIdentity(
            withings_userid=user.withings.oauth_userid,
            slack_alias=user.slack_alias,
        )
        if user
        else None
    )


async def get_oauth_data_by_withings_userid(
    db: AsyncSession,
    withings_userid: str,
) -> OAuthData:
    withings_user: models.WithingsUser = (
        await db.scalars(
            statement=select(models.WithingsUser).where(
                models.WithingsUser.oauth_userid == withings_userid
            )
        )
    ).one()
    return OAuthData(
        oauth_access_token=withings_user.oauth_access_token,
        oauth_refresh_token=withings_user.oauth_refresh_token,
        oauth_expiration_date=withings_user.oauth_expiration_date.replace(
            tzinfo=datetime.timezone.utc
        ),
    )


async def get_fitness_data_by_withings_userid(
    db: AsyncSession,
    withings_userid: str,
) -> FitnessData:
    withings_user: models.WithingsUser = (
        await db.scalars(
            statement=select(models.WithingsUser).where(
                models.WithingsUser.oauth_userid == withings_userid
            )
        )
    ).one()
    return FitnessData(
        last_weight_kg=withings_user.last_weight,
    )


async def get_user_by_withings_userid(
    db: AsyncSession,
    withings_userid: str,
) -> User:
    user: models.User = (
        await db.scalars(
            statement=select(models.User)
            .join(models.User.withings)
            .where(models.WithingsUser.oauth_userid == withings_userid)
        )
    ).one()
    return User(
        identity=UserIdentity(
            withings_userid=user.withings.oauth_userid,
            slack_alias=user.slack_alias,
        ),
        oauth_data=OAuthData(
            oauth_access_token=user.withings.oauth_access_token,
            oauth_refresh_token=user.withings.oauth_refresh_token,
            oauth_expiration_date=user.withings.oauth_expiration_date.replace(
                tzinfo=datetime.timezone.utc
            ),
        ),
        fitness_data=FitnessData(
            last_weight_kg=user.withings.last_weight,
        ),
    )


async def update_user_weight(
    db: AsyncSession,
    withings_userid: str,
    last_weight_kg: float,
):
    await db.execute(
        statement=update(models.WithingsUser)
        .where(models.WithingsUser.oauth_userid == withings_userid)
        .values(last_weight=last_weight_kg)
    )
    await db.commit()


async def update_oauth_data(
    db: AsyncSession,
    withings_userid: str,
    oauth_data: OAuthData,
):
    await db.execute(
        statement=update(models.WithingsUser)
        .where(models.WithingsUser.oauth_userid == withings_userid)
        .values(
            oauth_access_token=oauth_data.oauth_access_token,
            oauth_refresh_token=oauth_data.oauth_refresh_token,
            oauth_expiration_date=oauth_data.oauth_expiration_date,
        )
    )
    await db.commit()
