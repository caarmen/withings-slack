from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    slack_alias = Column(String, unique=True, index=True)
    oauth_access_token = Column(String(40))
    oauth_refresh_token = Column(String(40))
    oauth_userid = Column(String(40))
    oauth_expiration_date = Column(DateTime)
