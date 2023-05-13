from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from withingsslack.database import models


def get_user(
    db: Session,
    withings_oauth_userid: str = None,
    fitbit_oauth_userid: str = None,
    slack_alias: str = None,
) -> models.User:
    """
    Return the user with the given withings oauth user id.
    """
    if withings_oauth_userid:
        return (
            db.query(models.User)
            .join(models.User.withings)
            .filter(models.WithingsUser.oauth_userid == withings_oauth_userid)
            .one()
        )
    elif fitbit_oauth_userid:
        return (
            db.query(models.User)
            .join(models.User.fitbit)
            .filter(models.FitbitUser.oauth_userid == fitbit_oauth_userid)
            .one()
        )
    else:
        return (
            db.query(models.User).filter(models.User.slack_alias == slack_alias).one()
        )


def upsert_user(
    db: Session,
    withings_oauth_userid: str = None,
    fitbit_oauth_userid: str = None,
    data: dict = None,
    withings_data: dict = None,
    fitbit_data=None,
) -> models.User:
    try:
        if withings_oauth_userid:
            user = get_user(db, withings_oauth_userid=withings_oauth_userid)
        else:
            user = get_user(db, fitbit_oauth_userid=fitbit_oauth_userid)
        return update_user(
            db, user, data=data, withings_data=withings_data, fitbit_data=fitbit_data
        )
    except NoResultFound:
        # TODO simplify this
        try:
            user = get_user(db, slack_alias=data["slack_alias"])
            return update_user(
                db,
                user,
                data=data,
                withings_data=withings_data,
                fitbit_data=fitbit_data,
            )
        except NoResultFound:
            return create_user(
                db,
                models.User(**data),
                withings_data=withings_data,
                fitbit_data=fitbit_data,
            )


def upsert_withings_data(
    db: Session,
    user_id: str,
    data: dict,
) -> models.WithingsUser:
    try:
        withings_user = (
            db.query(models.WithingsUser)
            .filter(models.WithingsUser.user_id == user_id)
            .one()
        )
        db.query(models.WithingsUser).filter_by(id=withings_user.id).update(data)
    except NoResultFound:
        withings_user = models.WithingsUser(user_id=user_id, **data)
        db.add(withings_user)
    db.commit()
    db.refresh(withings_user)
    return withings_user


def upsert_fitbit_data(
    db: Session,
    user_id: str,
    data: dict,
) -> models.FitbitUser:
    try:
        fitbit_user = (
            db.query(models.FitbitUser)
            .filter(models.FitbitUser.user_id == user_id)
            .one()
        )
        db.query(models.FitbitUser).filter_by(id=fitbit_user.id).update(data)
    except NoResultFound:
        fitbit_user = models.FitbitUser(user_id=user_id, **data)
        db.add(fitbit_user)
    db.commit()
    db.refresh(fitbit_user)
    return fitbit_user


def create_user(
    db: Session,
    user: models.User,
    withings_data: dict,
    fitbit_data: dict,
) -> models.User:
    db.add(user)
    db.commit()
    if withings_data:
        withings_user = models.WithingsUser(
            user_id=user.id,
            **withings_data,
        )
        db.add(withings_user)
    if fitbit_data:
        fitbit_user = models.FitbitUser(user_id=user.id, **fitbit_data)
        db.add(fitbit_user)
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    user: models.User,
    data: dict = None,
    withings_data: dict = None,
    fitbit_data: dict = None,
) -> models.User:
    if data:
        db.query(models.User).filter_by(id=user.id).update(data)
    if withings_data:
        upsert_withings_data(db, user_id=user.id, data=withings_data)
    if fitbit_data:
        upsert_fitbit_data(db, user_id=user.id, data=fitbit_data)
    db.commit()
    db.refresh(user)
    return user
