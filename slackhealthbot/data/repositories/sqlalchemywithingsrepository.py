import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.exceptions import UnknownUserException
from slackhealthbot.core.models import OAuthFields
from slackhealthbot.data.database import models
from slackhealthbot.domain.localrepository.localwithingsrepository import (
    FitnessData,
    LocalWithingsRepository,
    User,
    UserIdentity,
)


class SQLAlchemyWithingsRepository(LocalWithingsRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(
        self, slack_alias: str, withings_userid: str, oauth_data: OAuthFields
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

        withings_user = models.WithingsUser(
            user_id=user.id,
            oauth_userid=withings_userid,
            oauth_access_token=oauth_data.oauth_access_token,
            oauth_refresh_token=oauth_data.oauth_refresh_token,
            oauth_expiration_date=oauth_data.oauth_expiration_date,
        )
        self.db.add(withings_user)
        await self.db.commit()
        await self.db.refresh(withings_user)

        return User(
            identity=UserIdentity(
                withings_userid=withings_user,
                slack_alias=slack_alias,
            ),
            oauth_data=OAuthFields(
                oauth_userid=withings_user.oauth_userid,
                oauth_access_token=withings_user.oauth_access_token,
                oauth_refresh_token=withings_user.oauth_refresh_token,
                oauth_expiration_date=withings_user.oauth_expiration_date.replace(
                    tzinfo=datetime.timezone.utc
                ),
            ),
            fitness_data=FitnessData(),
        )

    async def get_user_identity_by_withings_userid(
        self,
        withings_userid: str,
    ) -> UserIdentity | None:
        user: models.User = (
            await self.db.scalars(
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
        self,
        withings_userid: str,
    ) -> OAuthFields:
        withings_user: models.WithingsUser = (
            await self.db.scalars(
                statement=select(models.WithingsUser).where(
                    models.WithingsUser.oauth_userid == withings_userid
                )
            )
        ).one()
        return OAuthFields(
            oauth_userid=withings_userid,
            oauth_access_token=withings_user.oauth_access_token,
            oauth_refresh_token=withings_user.oauth_refresh_token,
            oauth_expiration_date=withings_user.oauth_expiration_date.replace(
                tzinfo=datetime.timezone.utc
            ),
        )

    async def get_fitness_data_by_withings_userid(
        self,
        withings_userid: str,
    ) -> FitnessData:
        withings_user: models.WithingsUser = (
            await self.db.scalars(
                statement=select(models.WithingsUser).where(
                    models.WithingsUser.oauth_userid == withings_userid
                )
            )
        ).one()
        return FitnessData(
            last_weight_kg=withings_user.last_weight,
        )

    async def get_user_by_withings_userid(
        self,
        withings_userid: str,
    ) -> User:
        user: models.User = (
            await self.db.scalars(
                statement=select(models.User)
                .join(models.User.withings)
                .where(models.WithingsUser.oauth_userid == withings_userid)
            )
        ).one_or_none()
        if not user:
            raise UnknownUserException
        return User(
            identity=UserIdentity(
                withings_userid=user.withings.oauth_userid,
                slack_alias=user.slack_alias,
            ),
            oauth_data=OAuthFields(
                oauth_userid=withings_userid,
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
        self,
        withings_userid: str,
        last_weight_kg: float,
    ):
        await self.db.execute(
            statement=update(models.WithingsUser)
            .where(models.WithingsUser.oauth_userid == withings_userid)
            .values(last_weight=last_weight_kg)
        )
        await self.db.commit()

    async def update_oauth_data(
        self,
        withings_userid: str,
        oauth_data: OAuthFields,
    ):
        await self.db.execute(
            statement=update(models.WithingsUser)
            .where(models.WithingsUser.oauth_userid == withings_userid)
            .values(
                oauth_access_token=oauth_data.oauth_access_token,
                oauth_refresh_token=oauth_data.oauth_refresh_token,
                oauth_expiration_date=oauth_data.oauth_expiration_date,
            )
        )
        await self.db.commit()
