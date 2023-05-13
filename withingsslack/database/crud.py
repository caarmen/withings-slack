from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from withingsslack.database import models


def get_user(db: Session, withings_oauth_userid: str) -> models.User:
    """
    Return the user with the given withings oauth user id.
    """
    return (
        db.query(models.User)
        .join(models.User.withings)
        .filter(models.WithingsUser.oauth_userid == withings_oauth_userid)
        .one()
    )


def upsert_user(
    db: Session,
    withings_oauth_userid: str,
    data: dict = None,
    withings_data: dict = None,
) -> models.User:
    try:
        user = get_user(db, withings_oauth_userid=withings_oauth_userid)
        return update_user(db, user, data=data, withings_data=withings_data)
    except NoResultFound:
        return create_user(
            db,
            models.User(**data),
            withings_data=withings_data,
        )


def create_user(db: Session, user: models.User, withings_data: dict) -> models.User:
    db.add(user)
    db.commit()
    withings_user = models.WithingsUser(
        user_id=user.id,
        **withings_data,
    )
    db.add(withings_user)
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    user: models.User,
    data: dict = None,
    withings_data: dict = None,
) -> models.User:
    if data:
        db.query(models.User).filter_by(id=user.id).update(data)
    if withings_data:
        db.query(models.WithingsUser).filter_by(user_id=user.id).update(withings_data)
    db.commit()
    db.refresh(user)
    return user
