from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import AsyncContextManager, Callable

from fastapi import Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.data.database.connection import SessionLocal
from slackhealthbot.data.repositories.fitbitdbrepository import FitbitDbRepository
from slackhealthbot.data.repositories.withingsdbrepository import WithingsDbRepository
from slackhealthbot.domain.repository.fitbitrepository import FitbitRepository
from slackhealthbot.domain.repository.withingsrepository import WithingsRepository

_ctx_db = ContextVar("ctx_db")
_ctx_withings_repository = ContextVar("withings_repository")
_ctx_fitbit_repository = ContextVar("fitbit_repository")


async def get_db():
    db = SessionLocal()
    try:
        # We need to access the db session without having access to
        # fastapi's dependency injection. This happens when our update_token()
        # authlib function is called.
        # Set the db in a ContextVar to allow accessing it outside a fastapi route.
        _ctx_db.set(db)
        yield db
    finally:
        await db.close()
        _ctx_db.set(None)


async def get_withings_repository(
    db: AsyncSession = Depends(get_db),
) -> WithingsRepository:
    repo = WithingsDbRepository(db=db)
    _ctx_withings_repository.set(repo)
    yield repo
    _ctx_withings_repository.set(None)


def request_context_withings_repository() -> WithingsRepository:
    return _ctx_withings_repository.get()


async def get_fitbit_repository(
    db: AsyncSession = Depends(get_db),
) -> FitbitRepository:
    repo = FitbitDbRepository(db=db)
    _ctx_fitbit_repository.set(repo)
    yield repo
    _ctx_fitbit_repository.set(None)


def request_context_fitbit_repository() -> FitbitRepository:
    return _ctx_fitbit_repository.get()


# TODO move this
def fitbit_repository_factory(
    db: AsyncSession | None = None,
) -> Callable[[], AsyncContextManager[FitbitRepository]]:
    @asynccontextmanager
    async def ctx_mgr() -> FitbitRepository:
        autoclose_db = False
        _db = db
        if _db is None:
            _db = SessionLocal()
            autoclose_db = True
        repo = FitbitDbRepository(db=_db)
        _ctx_fitbit_repository.set(repo)
        yield repo
        _ctx_fitbit_repository.set(None)
        if autoclose_db:
            await _db.close()

    return ctx_mgr


templates = Jinja2Templates(directory="templates")
