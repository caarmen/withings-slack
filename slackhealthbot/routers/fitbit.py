import datetime
import logging

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import SleepData
from slackhealthbot.domain.fitbit import (
    usecase_login_user,
    usecase_process_new_activity,
    usecase_process_new_sleep,
)
from slackhealthbot.repositories import fitbitrepository
from slackhealthbot.repositories.fitbitrepository import UserIdentity
from slackhealthbot.routers.dependencies import get_db, templates
from slackhealthbot.services import slack
from slackhealthbot.services.exceptions import UserLoggedOutException
from slackhealthbot.services.oauth.config import oauth
from slackhealthbot.settings import fitbit_oauth_settings as settings

router = APIRouter()


@router.get("/v1/fitbit-authorization/{slack_alias}")
async def get_fitbit_authorization(slack_alias: str, request: Request):
    request.session["slack_alias"] = slack_alias
    return await oauth.create_client(settings.name).authorize_redirect(request)


@router.get("/fitbit-notification-webhook/")
def validate_fitbit_notification_webhook(verify: str | None = None):
    # See the fitbit verification doc:
    # https://dev.fitbit.com/build/reference/web-api/developer-guide/using-subscriptions/#Verifying-a-Subscriber
    if verify == settings.subscriber_verification_code:
        return Response(status_code=204)
    return Response(status_code=404)


@router.get("/fitbit-oauth-webhook/")
async def fitbit_oauth_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    token: dict = await oauth.create_client(settings.name).authorize_access_token(
        request
    )
    await usecase_login_user.do(
        db=db, token=token, slack_alias=request.session.pop("slack_alias")
    )
    return templates.TemplateResponse(
        request=request, name="login_complete.html", context={"provider": "fitbit"}
    )


class FitbitNotification(BaseModel):
    collectionType: str | None = None
    date: datetime.date | None = None
    ownerId: str | None = None
    ownerType: str | None = None
    subscriptionId: str | None = None


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


@router.post("/fitbit-notification-webhook/")
async def fitbit_notification_webhook(
    notifications: list[FitbitNotification],
    db: AsyncSession = Depends(get_db),
):
    logging.info(f"fitbit_notification_webhook: {notifications}")
    for notification in notifications:
        if _is_fitbit_notification_processed(notification):
            logging.info("fitbit_notificaiton_webhook: skipping duplicate notification")
            continue

        # TODO User
        user_identity: UserIdentity = (
            await fitbitrepository.get_user_identity_by_fitbit_userid(
                db,
                fitbit_userid=notification.ownerId,
            )
        )
        try:
            if notification.collectionType == "sleep":
                new_sleep_data: SleepData = await usecase_process_new_sleep.do(
                    db,
                    fitbit_userid=notification.ownerId,
                    when=notification.date,
                )
                if new_sleep_data:
                    _mark_fitbit_notification_processed(notification)
            elif notification.collectionType == "activities":
                activity_history = await usecase_process_new_activity.do(
                    db=db,
                    fitbit_userid=notification.ownerId,
                    when=datetime.datetime.now(),
                )
                if activity_history:
                    _mark_fitbit_notification_processed(notification)
        except UserLoggedOutException:
            await slack.post_user_logged_out(
                slack_alias=user_identity.slack_alias,
                service="fitbit",
            )
            break
    return Response(status_code=status.HTTP_204_NO_CONTENT)
