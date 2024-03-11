import datetime
import logging

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel

from slackhealthbot.core.exceptions import UserLoggedOutException
from slackhealthbot.domain.localrepository.localfitbitrepository import (
    LocalFitbitRepository,
)
from slackhealthbot.domain.usecases.fitbit import (
    usecase_login_user,
    usecase_post_user_logged_out,
    usecase_process_new_activity,
    usecase_process_new_sleep,
)
from slackhealthbot.oauth.config import oauth
from slackhealthbot.routers.dependencies import get_fitbit_repository, templates
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
async def fitbit_oauth_webhook(
    request: Request,
    repo: LocalFitbitRepository = Depends(get_fitbit_repository),
):
    token: dict = await oauth.create_client(settings.name).authorize_access_token(
        request
    )
    await usecase_login_user.do(
        repo=repo, token=token, slack_alias=request.session.pop("slack_alias")
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
    repo: LocalFitbitRepository = Depends(get_fitbit_repository),
):
    logging.info(f"fitbit_notification_webhook: {notifications}")
    for notification in notifications:
        if _is_fitbit_notification_processed(notification):
            logging.info("fitbit_notificaiton_webhook: skipping duplicate notification")
            continue

        try:
            if notification.collectionType == "sleep":
                new_sleep_data = await usecase_process_new_sleep.do(
                    repo=repo,
                    fitbit_userid=notification.ownerId,
                    when=notification.date,
                )
                if new_sleep_data:
                    _mark_fitbit_notification_processed(notification)
            elif notification.collectionType == "activities":
                activity_history = await usecase_process_new_activity.do(
                    repo=repo,
                    fitbit_userid=notification.ownerId,
                    when=datetime.datetime.now(),
                )
                if activity_history:
                    _mark_fitbit_notification_processed(notification)
        except UserLoggedOutException:
            await usecase_post_user_logged_out.do(
                repo=repo,
                fitbit_userid=notification.ownerId,
            )
            break
    return Response(status_code=status.HTTP_204_NO_CONTENT)
