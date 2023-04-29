from sqlalchemy.orm import Session

from withingsslack.database import models


def get_user(db: Session, oauth_userid: str) -> models.User:
    return (
        db.query(models.User).filter(models.User.oauth_userid == oauth_userid).first()
    )


def get_or_create_user(db: Session, oauth_userid: str) -> models.User:
    user = get_user(db, oauth_userid=oauth_userid)
    if not user:
        user = create_user(db, models.User(oauth_userid=oauth_userid))
    return user


def create_user(db: Session, user: models.User) -> models.User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: models.User, data: dict) -> models.User:
    db.query(models.User).filter_by(id=user.id).update(data)
    db.commit()
    db.refresh(user)
    return user
