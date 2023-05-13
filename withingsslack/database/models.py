from datetime import datetime
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

from typing import Optional

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    slack_alias: Mapped[str] = mapped_column(unique=True, index=True)
    oauth_access_token: Mapped[Optional[str]] = mapped_column(String(40))
    oauth_refresh_token: Mapped[Optional[str]] = mapped_column(String(40))
    oauth_userid: Mapped[str] = mapped_column(String(40))
    oauth_expiration_date: Mapped[Optional[datetime]] = mapped_column()
