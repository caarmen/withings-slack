from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

Base = declarative_base()


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        onupdate=func.now(), server_default=func.now()
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    slack_alias: Mapped[str] = mapped_column(unique=True, index=True)
    withings: Mapped["WithingsUser"] = relationship(
        back_populates="user", lazy="joined", join_depth=2
    )
    fitbit: Mapped["FitbitUser"] = relationship(
        back_populates="user", lazy="joined", join_depth=2
    )


class WithingsUser(TimestampMixin, Base):
    __tablename__ = "withings_users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    user: Mapped["User"] = relationship(
        back_populates="withings", lazy="joined", join_depth=2
    )
    oauth_access_token: Mapped[Optional[str]] = mapped_column(String(40))
    oauth_refresh_token: Mapped[Optional[str]] = mapped_column(String(40))
    oauth_userid: Mapped[str] = mapped_column(String(40))
    oauth_expiration_date: Mapped[Optional[datetime]] = mapped_column()
    last_weight: Mapped[Optional[float]] = mapped_column(Float())


class FitbitUser(TimestampMixin, Base):
    __tablename__ = "fitbit_users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    user: Mapped["User"] = relationship(
        back_populates="fitbit", lazy="joined", join_depth=2
    )
    oauth_access_token: Mapped[Optional[str]] = mapped_column(String(40))
    oauth_refresh_token: Mapped[Optional[str]] = mapped_column(String(40))
    oauth_userid: Mapped[str] = mapped_column(String(40))
    oauth_expiration_date: Mapped[Optional[datetime]] = mapped_column()
    last_sleep_start_time: Mapped[Optional[datetime]] = mapped_column()
    last_sleep_end_time: Mapped[Optional[datetime]] = mapped_column()
    last_sleep_sleep_minutes: Mapped[Optional[int]] = mapped_column()
    last_sleep_wake_minutes: Mapped[Optional[int]] = mapped_column()
