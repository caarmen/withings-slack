from contextvars import ContextVar

from fastapi import Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.data.database.connection import SessionLocal, ctx_db
from slackhealthbot.data.repositories.withingsdbrepository import WithingsDbRepository
from slackhealthbot.domain.repository.withingsrepository import WithingsRepository

_ctx_withings_repository = ContextVar("withings_repository")


async def get_db():
    db = SessionLocal()
    try:
        # We need to access the db session without having access to
        # fastapi's dependency injection. This happens when our update_token()
        # authlib function is called.
        # Set the db in a ContextVar to allow accessing it outside a fastapi route.
        ctx_db.set(db)
        yield db
    finally:
        await db.close()
        ctx_db.set(None)


async def get_withings_repository(
    db: AsyncSession = Depends(get_db),
) -> WithingsRepository:
    repo = WithingsDbRepository(db=db)
    _ctx_withings_repository.set(repo)
    yield repo
    _ctx_withings_repository.set(None)


def request_context_withings_repository() -> WithingsRepository:
    return _ctx_withings_repository.get()


templates = Jinja2Templates(directory="templates")
