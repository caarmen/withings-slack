from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

Base = declarative_base()


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        onupdate=func.now(), server_default=func.now()
    )


class User(TimestampMixin, AsyncAttrs, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    slack_alias: Mapped[str] = mapped_column(unique=True, index=True)
    withings: Mapped["WithingsUser"] = relationship(
        back_populates="user", lazy="joined", join_depth=2
    )
    fitbit: Mapped["FitbitUser"] = relationship(
        back_populates="user", lazy="joined", join_depth=2
    )


class WithingsUser(TimestampMixin, AsyncAttrs, Base):
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


class FitbitUser(TimestampMixin, AsyncAttrs, Base):
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
    latest_activities: Mapped[list["FitbitLatestActivity"]] = relationship(
        back_populates="fitbit_user", lazy="select", cascade="all, delete-orphan"
    )


class FitbitLatestActivity(TimestampMixin, AsyncAttrs, Base):
    __tablename__ = "fitbit_latest_activities"
    __table_args__ = (UniqueConstraint("fitbit_user_id", "type_id"),)
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    log_id: Mapped[int] = mapped_column(unique=True)
    type_id: Mapped[int] = mapped_column()
    total_minutes: Mapped[int] = mapped_column()
    calories: Mapped[int] = mapped_column()
    fat_burn_minutes: Mapped[Optional[int]] = mapped_column()
    cardio_minutes: Mapped[Optional[int]] = mapped_column()
    peak_minutes: Mapped[Optional[int]] = mapped_column()
    out_of_range_minutes: Mapped[Optional[int]] = mapped_column()
    fitbit_user: Mapped[FitbitUser] = relationship(
        back_populates="latest_activities", lazy="joined"
    )
    fitbit_user_id: Mapped[int] = mapped_column(
        ForeignKey("fitbit_users.id", ondelete="CASCADE")
    )
