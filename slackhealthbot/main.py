import random
import string
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Response
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from slackhealthbot import logger, scheduler
from slackhealthbot.domain.fitbit.usecase_update_user_oauth import (
    do as fitbit_usecase_update_user_oauth,
)
from slackhealthbot.domain.withings.usecase_update_user_oauth import (
    do as withings_usecase_update_user_oauth,
)
from slackhealthbot.routers.fitbit import router as fitbit_router
from slackhealthbot.routers.withings import router as withings_router
from slackhealthbot.services.oauth import fitbitconfig as oauth_fitbit
from slackhealthbot.services.oauth import withingsconfig as oauth_withings
from slackhealthbot.settings import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.update_external_loggers()
    if settings.fitbit_poll_enabled:
        await scheduler.schedule_fitbit_poll(delay_s=10)
    oauth_withings.configure(withings_usecase_update_user_oauth)
    oauth_fitbit.configure(fitbit_usecase_update_user_oauth)
    yield


app = FastAPI(
    middleware=[
        Middleware(logger.LoggerMiddleware),
        Middleware(
            SessionMiddleware,
            secret_key="".join(
                random.choice(string.ascii_lowercase) for i in range(32)
            ),
        ),
    ],
    lifespan=lifespan,
)

app.include_router(withings_router)
app.include_router(fitbit_router)


@app.head("/")
def validate_root():
    return Response()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=logger.get_uvicorn_log_config(),
    )
