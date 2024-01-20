import dataclasses

from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.database import models


async def get_user(
    db: AsyncSession,
    withings_oauth_userid: str = None,
    fitbit_oauth_userid: str = None,
    slack_alias: str = None,
) -> models.User:
    """
    Return the user with the given withings oauth user id.
    """
    if withings_oauth_userid:
        return (
            await db.scalars(
                statement=select(models.User)
                .join(models.User.withings)
                .where(models.WithingsUser.oauth_userid == withings_oauth_userid)
            )
        ).one()
    elif fitbit_oauth_userid:
        return (
            await db.scalars(
                statement=select(models.User)
                .join(models.User.fitbit)
                .where(models.FitbitUser.oauth_userid == fitbit_oauth_userid)
            )
        ).one()
    else:
        return (
            await db.scalars(
                statement=select(models.User).where(
                    models.User.slack_alias == slack_alias
                )
            )
        ).one()


@dataclasses.dataclass
class UserUpsert:
    withings_oauth_userid: str = None
    fitbit_oauth_userid: str = None
    data: dict = None
    withings_data: dict = None
    fitbit_data: dict = None


async def upsert_user(
    db: AsyncSession,
    user_upsert: UserUpsert,
) -> models.User:
    try:
        if user_upsert.withings_oauth_userid:
            user = await get_user(
                db, withings_oauth_userid=user_upsert.withings_oauth_userid
            )
        else:
            user = await get_user(
                db, fitbit_oauth_userid=user_upsert.fitbit_oauth_userid
            )
        return await update_user(
            db,
            user,
            data=user_upsert.data,
            withings_data=user_upsert.withings_data,
            fitbit_data=user_upsert.fitbit_data,
        )
    except NoResultFound:
        # TODO simplify this
        try:
            user = await get_user(db, slack_alias=user_upsert.data["slack_alias"])
            return await update_user(
                db,
                user,
                data=user_upsert.data,
                withings_data=user_upsert.withings_data,
                fitbit_data=user_upsert.fitbit_data,
            )
        except NoResultFound:
            return await create_user(
                db,
                models.User(**user_upsert.data),
                withings_data=user_upsert.withings_data,
                fitbit_data=user_upsert.fitbit_data,
            )


async def upsert_withings_data(
    db: AsyncSession,
    user_id: str,
    data: dict,
) -> models.WithingsUser:
    try:
        withings_user: models.WithingsUser = (
            await db.scalars(
                statement=select(models.WithingsUser).where(
                    models.WithingsUser.user_id == user_id
                )
            )
        ).one()
        await db.execute(
            statement=update(models.WithingsUser)
            .where(models.WithingsUser.id == withings_user.id)
            .values(**data)
        )
    except NoResultFound:
        withings_user = models.WithingsUser(user_id=user_id, **data)
        db.add(withings_user)
    await db.commit()
    await db.refresh(withings_user)
    return withings_user


async def upsert_fitbit_data(
    db: AsyncSession,
    user_id: str,
    data: dict,
) -> models.FitbitUser:
    try:
        fitbit_user = (
            await db.scalars(
                statement=select(models.FitbitUser).where(
                    models.FitbitUser.user_id == user_id
                )
            )
        ).one()
        await db.execute(
            statement=update(models.FitbitUser)
            .where(models.FitbitUser.id == fitbit_user.id)
            .values(**data)
        )
    except NoResultFound:
        fitbit_user = models.FitbitUser(user_id=user_id, **data)
        db.add(fitbit_user)
    await db.commit()
    await db.refresh(fitbit_user)
    return fitbit_user


async def upsert_fitbit_activity_data(
    db: AsyncSession,
    fitbit_user_id: str,
    type_id: int,
    data: dict,
):
    try:
        fitbit_activity = (
            await db.scalars(
                statement=select(models.FitbitLatestActivity).where(
                    models.FitbitLatestActivity.fitbit_user_id == fitbit_user_id
                    and models.FitbitLatestActivity.type_id == type_id
                )
            )
        ).one()
        await db.execute(
            statement=update(models.FitbitLatestActivity)
            .where(
                models.FitbitLatestActivity.fitbit_user_id == fitbit_user_id
                and models.FitbitLatestActivity.type_id == type_id
            )
            .values(**data)
        )
    except NoResultFound:
        fitbit_activity = models.FitbitLatestActivity(
            fitbit_user_id=fitbit_user_id, type_id=type_id, **data
        )
        db.add(fitbit_activity)

    await db.commit()


async def create_user(
    db: AsyncSession,
    user: models.User,
    withings_data: dict,
    fitbit_data: dict,
) -> models.User:
    db.add(user)
    await db.commit()
    await db.refresh(user)
    if withings_data:
        withings_user = models.WithingsUser(
            user_id=user.id,
            **withings_data,
        )
        db.add(withings_user)
    if fitbit_data:
        fitbit_user = models.FitbitUser(user_id=user.id, **fitbit_data)
        db.add(fitbit_user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession,
    user: models.User,
    data: dict = None,
    withings_data: dict = None,
    fitbit_data: dict = None,
) -> models.User:
    if data:
        await db.execute(
            statement=update(models.User)
            .where(models.User.id == user.id)
            .values(**data)
        )
    if withings_data:
        await upsert_withings_data(db, user_id=user.id, data=withings_data)
    if fitbit_data:
        await upsert_fitbit_data(db, user_id=user.id, data=fitbit_data)
    await db.commit()
    await db.refresh(user)
    return user
