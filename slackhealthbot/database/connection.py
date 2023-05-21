from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from slackhealthbot.settings import settings

connection_url = f"sqlite:///{settings.database_path}"
Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(
    connection_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
