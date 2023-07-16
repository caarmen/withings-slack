from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from slackhealthbot.settings import settings

connection_url = f"sqlite+aiosqlite:///{settings.database_path}"
Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
engine = create_async_engine(
    connection_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, future=True
)
