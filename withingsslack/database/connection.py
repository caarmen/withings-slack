from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from withingsslack.settings import settings


engine = create_engine(
    f"sqlite:///{settings.database_path}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
