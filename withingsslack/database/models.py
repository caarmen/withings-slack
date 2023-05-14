from datetime import datetime
from sqlalchemy import ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import Optional

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    slack_alias: Mapped[str] = mapped_column(unique=True, index=True)
    withings: Mapped["WithingsUser"] = relationship(back_populates="user")
    fitbit: Mapped["FitbitUser"] = relationship(back_populates="user")


class WithingsUser(Base):
    __tablename__ = "withings_users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    user: Mapped["User"] = relationship(back_populates="withings")
    oauth_access_token: Mapped[Optional[str]] = mapped_column(String(40))
    oauth_refresh_token: Mapped[Optional[str]] = mapped_column(String(40))
    oauth_userid: Mapped[str] = mapped_column(String(40))
    oauth_expiration_date: Mapped[Optional[datetime]] = mapped_column()


class FitbitUser(Base):
    __tablename__ = "fitbit_users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    user: Mapped["User"] = relationship(back_populates="fitbit")
    oauth_access_token: Mapped[Optional[str]] = mapped_column(String(40))
    oauth_refresh_token: Mapped[Optional[str]] = mapped_column(String(40))
    oauth_userid: Mapped[str] = mapped_column(String(40))
    oauth_expiration_date: Mapped[Optional[datetime]] = mapped_column()
