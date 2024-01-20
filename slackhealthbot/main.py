import datetime
import logging
import random
import string
from contextlib import asynccontextmanager
from typing import Annotated, Optional

import uvicorn
from fastapi import Depends, FastAPI, Form, Request, Response, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from slackhealthbot import logger, scheduler
from slackhealthbot.database import crud
from slackhealthbot.database.connection import SessionLocal, ctx_db
from slackhealthbot.services import models as svc_models
from slackhealthbot.services import slack
from slackhealthbot.services.exceptions import UserLoggedOutException
from slackhealthbot.services.fitbit import api as fitbit_api
from slackhealthbot.services.fitbit import oauth as fitbit_oauth
from slackhealthbot.services.fitbit import service as fitbit_service
from slackhealthbot.services.oauth import oauth
from slackhealthbot.services.withings import api as withings_api
from slackhealthbot.services.withings import oauth as withings_oauth
from slackhealthbot.settings import settings

LOGIN_COMPLETE_CONTENT = """
    <html>
        <head>
            <title>Login complete</title>
        </head>
        <body>
            <h1>Congrats, Login complete</h1>
        </body>
    </html>
    """


async def get_db():
    db = SessionLocal()
    try:
        # We need to access the db session without having access to
        # fastapi's dependency injection. This happens when our update_token()
        # authlib function is called.
        # Set the db in a ContextVar to allow accessing it outside of a fastapi route.
        ctx_db.set(db)
        yield db
    finally:
        await db.close()
        ctx_db.set(None)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.update_external_loggers()
    if settings.fitbit_poll_enabled:
        await scheduler.schedule_fitbit_poll(delay_s=10)
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


@app.get("/v1/withings-authorization/{slack_alias}")
async def get_withings_authorization(slack_alias: str, request: Request):
    return await oauth.create_oauth_url(
        provider=withings_oauth.PROVIDER,
        request=request,
        slack_alias=slack_alias,
        redirect_uri=settings.withings_redirect_uri,
    )


@app.get("/v1/fitbit-authorization/{slack_alias}")
async def get_fitbit_authorization(slack_alias: str, request: Request):
    return await oauth.create_oauth_url(
        provider=fitbit_oauth.PROVIDER, request=request, slack_alias=slack_alias
    )


@app.head("/")
def validate_root():
    return Response()


@app.head("/withings-oauth-webhook/")
def validate_withings_oauth_webhook():
    return Response()


@app.head("/withings-notification-webhook/")
def validate_withings_notification_webhook():
    return Response()


@app.get("/fitbit-notification-webhook/")
def validate_fitbit_notification_webhook(verify: str | None = None):
    # See the fitbit verification doc:
    # https://dev.fitbit.com/build/reference/web-api/developer-guide/using-subscriptions/#Verifying-a-Subscriber
    if verify == settings.fitbit_client_subscriber_verification_code:
        return Response(status_code=204)
    return Response(status_code=404)


@app.get("/fitbit-oauth-webhook/")
async def fitbit_oauth_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    token: dict = await oauth.fetch_token(fitbit_oauth.PROVIDER, request)
    user = await fitbit_oauth.update_token(
        db=db, token=token, slack_alias=request.session.pop("slack_alias")
    )
    await fitbit_api.subscribe(user)
    return HTMLResponse(content=LOGIN_COMPLETE_CONTENT, status_code=status.HTTP_200_OK)


@app.get("/withings-oauth-webhook/")
async def withings_oauth_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    token: dict = await oauth.fetch_token(withings_oauth.PROVIDER, request)
    user = await withings_oauth.update_token(
        db=db, token=token, slack_alias=request.session.pop("slack_alias")
    )
    await withings_api.subscribe(user)
    return HTMLResponse(content=LOGIN_COMPLETE_CONTENT, status_code=status.HTTP_200_OK)


class FitbitNotification(BaseModel):
    collectionType: Optional[str] = None
    date: Optional[datetime.date] = None
    ownerId: Optional[str] = None
    ownerType: Optional[str] = None
    subscriptionId: Optional[str] = None


last_processed_fitbit_notification_per_user: dict[str, datetime.datetime] = {}

DEBOUNCE_NOTIFICATION_DELAY_S = 10


def _is_fitbit_notification_processed(notification: FitbitNotification):
    # Fitbit often calls multiple times for the same event.
    # Ignore this notification if we just processed one recently.
    now = datetime.datetime.now()
    last_fitbit_notification_datetime = last_processed_fitbit_notification_per_user.get(
        notification.ownerId
    )
    already_processed = (
        last_fitbit_notification_datetime
        and (now - last_fitbit_notification_datetime).seconds
        < DEBOUNCE_NOTIFICATION_DELAY_S
    )
    return already_processed


def _mark_fitbit_notification_processed(notification: FitbitNotification):
    now = datetime.datetime.now()
    last_processed_fitbit_notification_per_user[notification.ownerId] = now


@app.post("/fitbit-notification-webhook/")
async def fitbit_notification_webhook(
    notifications: list[FitbitNotification],
    db: AsyncSession = Depends(get_db),
):
    logging.info(f"fitbit_notification_webhook: {notifications}")
    for notification in notifications:
        if _is_fitbit_notification_processed(notification):
            logging.info("fitbit_notificaiton_webhook: skipping duplicate notification")
            continue

        user = await crud.get_user(db, fitbit_oauth_userid=notification.ownerId)
        try:
            if notification.collectionType == "sleep":
                sleep_data = await fitbit_api.get_sleep(
                    user=user,
                    when=notification.date,
                )
                if sleep_data:
                    _mark_fitbit_notification_processed(notification)
                    last_sleep_data = svc_models.user_last_sleep_data(user.fitbit)
                    await fitbit_service.save_new_sleep_data(db, user, sleep_data)
                    await slack.post_sleep(
                        slack_alias=user.slack_alias,
                        new_sleep_data=sleep_data,
                        last_sleep_data=last_sleep_data,
                    )
            elif notification.collectionType == "activities":
                activity_history = await fitbit_service.get_activity(
                    db=db,
                    user=user,
                    when=datetime.datetime.now(),
                )
                if activity_history:
                    _mark_fitbit_notification_processed(notification)
                    await slack.post_activity(
                        slack_alias=user.slack_alias,
                        activity_history=activity_history,
                    )
        except UserLoggedOutException:
            await slack.post_user_logged_out(
                slack_alias=user.slack_alias,
                service="fitbit",
            )
            break
    return Response(status_code=status.HTTP_204_NO_CONTENT)


last_processed_withings_notification_per_user = {}


@app.post("/withings-notification-webhook/")
async def withings_notification_webhook(
    userid: Annotated[str, Form()],
    startdate: Annotated[int, Form()],
    enddate: Annotated[int, Form()],
    db: AsyncSession = Depends(get_db),
):
    logging.info(
        "withings_notification_webhook: "
        + f"userid={userid}, startdate={startdate}, enddate={enddate}"
    )
    if last_processed_withings_notification_per_user.get(userid, None) != (
        startdate,
        enddate,
    ):
        user = await crud.get_user(db, withings_oauth_userid=userid)
        try:
            last_weight_data = await withings_api.get_last_weight(
                db,
                userid=userid,
                startdate=startdate,
                enddate=enddate,
            )
        except UserLoggedOutException:
            await slack.post_user_logged_out(
                slack_alias=user.slack_alias,
                service="withings",
            )
        else:
            if last_weight_data:
                last_processed_withings_notification_per_user[userid] = (
                    startdate,
                    enddate,
                )
                await crud.update_user(
                    db, user, withings_data={"last_weight": last_weight_data.weight_kg}
                )
                await slack.post_weight(last_weight_data)
    else:
        logging.info("Ignoring duplicate withings notification")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=logger.get_uvicorn_log_config(),
    )
