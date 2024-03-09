import datetime

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import OAuthFields
from slackhealthbot.data.database import models
from slackhealthbot.domain.models.activity import (
    ActivityData,
    ActivityZone,
    ActivityZoneMinutes,
    TopActivityStats,
)
from slackhealthbot.domain.models.sleep import SleepData
from slackhealthbot.domain.repository.fitbitrepository import (
    FitbitRepository,
    User,
    UserIdentity,
)


class FitbitDbRepository(FitbitRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(
        self,
        slack_alias: str,
        fitbit_userid: str,
        oauth_data: OAuthFields,
    ) -> User:
        user = (
            await self.db.scalars(
                statement=select(models.User).where(
                    models.User.slack_alias == slack_alias
                )
            )
        ).one_or_none()
        if not user:
            user = models.User(slack_alias=slack_alias)
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

        fitbit_user = models.FitbitUser(
            user_id=user.id,
            oauth_userid=fitbit_userid,
            oauth_access_token=oauth_data.oauth_access_token,
            oauth_refresh_token=oauth_data.oauth_refresh_token,
            oauth_expiration_date=oauth_data.oauth_expiration_date,
        )
        self.db.add(fitbit_user)
        await self.db.commit()
        await self.db.refresh(fitbit_user)

        return User(
            identity=UserIdentity(
                fitbit_userid=fitbit_user.oauth_userid,
                slack_alias=slack_alias,
            ),
            oauth_data=OAuthFields(
                oauth_userid=fitbit_userid,
                oauth_access_token=fitbit_user.oauth_access_token,
                oauth_refresh_token=fitbit_user.oauth_refresh_token,
                oauth_expiration_date=fitbit_user.oauth_expiration_date.replace(
                    tzinfo=datetime.timezone.utc
                ),
            ),
        )

    async def get_user_identity_by_fitbit_userid(
        self,
        fitbit_userid: str,
    ) -> UserIdentity | None:
        user: models.User = (
            await self.db.scalars(
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
        self,
    ) -> list[UserIdentity]:
        users = await self.db.scalars(
            statement=select(models.User).join(models.User.fitbit)
        )
        return [
            UserIdentity(fitbit_userid=x.fitbit.oauth_userid, slack_alias=x.slack_alias)
            for x in users
        ]

    async def get_oauth_data_by_fitbit_userid(
        self,
        fitbit_userid: str,
    ) -> OAuthFields:
        fitbit_user: models.FitbitUser = (
            await self.db.scalars(
                statement=select(models.FitbitUser).where(
                    models.FitbitUser.oauth_userid == fitbit_userid
                )
            )
        ).one()
        return OAuthFields(
            oauth_userid=fitbit_user.oauth_userid,
            oauth_access_token=fitbit_user.oauth_access_token,
            oauth_refresh_token=fitbit_user.oauth_refresh_token,
            oauth_expiration_date=fitbit_user.oauth_expiration_date.replace(
                tzinfo=datetime.timezone.utc
            ),
        )

    async def get_user_by_fitbit_userid(
        self,
        fitbit_userid: str,
    ) -> User:
        user: models.User = (
            await self.db.scalars(
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
            oauth_data=OAuthFields(
                oauth_userid=fitbit_userid,
                oauth_access_token=user.fitbit.oauth_access_token,
                oauth_refresh_token=user.fitbit.oauth_refresh_token,
                oauth_expiration_date=user.fitbit.oauth_expiration_date.replace(
                    tzinfo=datetime.timezone.utc
                ),
            ),
        )

    async def get_latest_activity_by_user_and_type(
        self,
        fitbit_userid: str,
        type_id: int,
    ) -> ActivityData | None:
        db_activity: models.FitbitActivity = await self.db.scalar(
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
        return _db_activity_to_domain_activity(db_activity) if db_activity else None

    async def get_activity_by_user_and_log_id(
        self,
        fitbit_userid: str,
        log_id: int,
    ) -> ActivityData | None:
        db_activity: models.FitbitActivity = (
            await self.db.scalars(
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
        return _db_activity_to_domain_activity(db_activity) if db_activity else None

    async def create_activity_for_user(
        self,
        fitbit_userid: str,
        activity: ActivityData,
    ):
        user: models.FitbitUser = (
            await self.db.scalars(
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
            **{f"{x.zone}_minutes": x.minutes for x in activity.zone_minutes},
            fitbit_user_id=user.id,
        )
        self.db.add(fitbit_activity)
        await self.db.commit()

    async def update_sleep_for_user(
        self,
        fitbit_userid: str,
        sleep: SleepData,
    ):
        await self.db.execute(
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
        self,
        fitbit_userid: str,
    ) -> SleepData | None:
        fitbit_user: models.FitbitUser = (
            await self.db.scalars(
                statement=select(models.FitbitUser).where(
                    models.FitbitUser.oauth_userid == fitbit_userid
                )
            )
        ).one()
        if not fitbit_user or not fitbit_user.last_sleep_end_time:
            return None
        return SleepData(
            start_time=fitbit_user.last_sleep_start_time,
            end_time=fitbit_user.last_sleep_end_time,
            sleep_minutes=fitbit_user.last_sleep_sleep_minutes,
            wake_minutes=fitbit_user.last_sleep_wake_minutes,
        )

    async def update_oauth_data(
        self,
        fitbit_userid: str,
        oauth_data: OAuthFields,
    ):
        await self.db.execute(
            statement=update(models.FitbitUser)
            .where(models.FitbitUser.oauth_userid == fitbit_userid)
            .values(
                oauth_access_token=oauth_data.oauth_access_token,
                oauth_refresh_token=oauth_data.oauth_refresh_token,
                oauth_expiration_date=oauth_data.oauth_expiration_date,
            )
        )
        await self.db.commit()

    async def get_top_activity_stats_by_user_and_activity_type(
        self,
        fitbit_userid: str,
        type_id: int,
        since: datetime.datetime | None = None,
    ) -> TopActivityStats:

        columns = [
            models.FitbitActivity.calories,
            models.FitbitActivity.total_minutes,
            models.FitbitActivity.fat_burn_minutes,
            models.FitbitActivity.cardio_minutes,
            models.FitbitActivity.peak_minutes,
        ]
        conditions = [
            models.FitbitUser.oauth_userid == fitbit_userid,
            models.FitbitActivity.type_id == type_id,
        ]
        if since:
            conditions.append(models.FitbitActivity.updated_at >= since)

        subqueries = [
            select(func.max(column))
            .join(models.FitbitUser)
            .where(and_(*conditions))
            .label(f"top_{column.name}")
            for column in columns
        ]
        results = await self.db.execute(statement=select(*subqueries))
        # noinspection PyProtectedMember
        row = results.one()._asdict()

        return TopActivityStats(
            top_calories=row["top_calories"],
            top_total_minutes=row["top_total_minutes"],
            top_zone_minutes=[
                ActivityZoneMinutes(
                    zone=ActivityZone[x.upper()],
                    minutes=row.get(f"top_{x}_minutes"),
                )
                for x in ActivityZone
                if row.get(f"top_{x}_minutes")
            ],
        )


def _db_activity_to_domain_activity(
    db_activity: models.FitbitActivity,
) -> ActivityData:
    return ActivityData(
        log_id=db_activity.log_id,
        type_id=db_activity.type_id,
        calories=db_activity.calories,
        total_minutes=db_activity.total_minutes,
        zone_minutes=[
            ActivityZoneMinutes(
                zone=ActivityZone[x.upper()],
                minutes=getattr(db_activity, f"{x}_minutes"),
            )
            for x in ActivityZone
            if getattr(db_activity, f"{x}_minutes")
        ],
    )
