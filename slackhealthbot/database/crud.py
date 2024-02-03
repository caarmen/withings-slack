import dataclasses

from sqlalchemy import and_, desc, select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.database import models


async def get_user(
    db: AsyncSession,
    fitbit_oauth_userid: str = None,
    slack_alias: str = None,
) -> models.User:
    """
    Return the user with the given user id.
    """
    if fitbit_oauth_userid:
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
    fitbit_oauth_userid: str = None
    data: dict = None
    fitbit_data: dict = None


async def upsert_user(
    db: AsyncSession,
    user_upsert: UserUpsert,
) -> models.User:
    try:
        user = await get_user(db, fitbit_oauth_userid=user_upsert.fitbit_oauth_userid)
        return await update_user(
            db,
            user,
            data=user_upsert.data,
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
                fitbit_data=user_upsert.fitbit_data,
            )
        except NoResultFound:
            return await create_user(
                db,
                models.User(**user_upsert.data),
                fitbit_data=user_upsert.fitbit_data,
            )


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
                statement=select(models.FitbitActivity).where(
                    models.FitbitActivity.log_id == data["log_id"]
                )
            )
        ).one()
        await db.execute(
            statement=update(models.FitbitActivity)
            .where(models.FitbitActivity.log_id == data["log_id"])
            .values(**data)
        )
    except NoResultFound:
        fitbit_activity = models.FitbitActivity(
            fitbit_user_id=fitbit_user_id, type_id=type_id, **data
        )
        db.add(fitbit_activity)

    await db.commit()


async def get_latest_activity_by_user_and_type(
    db: AsyncSession,
    fitbit_user_id: str,
    type_id: int,
) -> models.FitbitActivity | None:
    return await db.scalar(
        statement=select(models.FitbitActivity)
        .where(
            and_(
                models.FitbitActivity.fitbit_user_id == fitbit_user_id,
                models.FitbitActivity.type_id == type_id,
            )
        )
        .order_by(desc(models.FitbitActivity.updated_at))
        .limit(1)
    )


async def get_activity_by_user_and_log_id(
    db: AsyncSession,
    fitbit_user_id: str,
    log_id: int,
) -> models.FitbitActivity | None:
    return (
        await db.scalars(
            statement=select(models.FitbitActivity).where(
                and_(
                    models.FitbitActivity.fitbit_user_id == fitbit_user_id,
                    models.FitbitActivity.log_id == log_id,
                )
            )
        )
    ).one_or_none()


async def create_user(
    db: AsyncSession,
    user: models.User,
    fitbit_data: dict,
) -> models.User:
    db.add(user)
    await db.commit()
    await db.refresh(user)
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
    fitbit_data: dict = None,
) -> models.User:
    if data:
        await db.execute(
            statement=update(models.User)
            .where(models.User.id == user.id)
            .values(**data)
        )
    if fitbit_data:
        await upsert_fitbit_data(db, user_id=user.id, data=fitbit_data)
    await db.commit()
    await db.refresh(user)
    return user
