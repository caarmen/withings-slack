import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response, status

from slackhealthbot.core.exceptions import UserLoggedOutException
from slackhealthbot.domain.localrepository.localwithingsrepository import (
    LocalWithingsRepository,
)
from slackhealthbot.domain.remoterepository.remoteslackrepository import (
    RemoteSlackRepository,
)
from slackhealthbot.domain.usecases.withings import (
    usecase_login_user,
    usecase_post_user_logged_out,
    usecase_process_new_weight,
)
from slackhealthbot.oauth.config import oauth
from slackhealthbot.routers.dependencies import (
    get_slack_repository,
    get_withings_repository,
    templates,
)
from slackhealthbot.settings import withings_oauth_settings as settings

router = APIRouter()


@router.head("/withings-oauth-webhook/")
def validate_withings_oauth_webhook():
    return Response()


@router.head("/withings-notification-webhook/")
def validate_withings_notification_webhook():
    return Response()


@router.get("/withings-oauth-webhook/")
async def withings_oauth_webhook(
    request: Request,
    repo: LocalWithingsRepository = Depends(get_withings_repository),
):
    token: dict = await oauth.create_client(settings.name).authorize_access_token(
        request
    )
    await usecase_login_user.do(
        repo=repo, token=token, slack_alias=request.session.pop("slack_alias")
    )
    return templates.TemplateResponse(
        request=request, name="login_complete.html", context={"provider": "withings"}
    )


@router.get("/v1/withings-authorization/{slack_alias}")
async def get_withings_authorization(slack_alias: str, request: Request):
    request.session["slack_alias"] = slack_alias
    return await oauth.create_client(settings.name).authorize_redirect(
        request, redirect_uri=settings.redirect_uri
    )


last_processed_withings_notification_per_user = {}


@router.post("/withings-notification-webhook/")
async def withings_notification_webhook(
    userid: Annotated[str, Form()],
    startdate: Annotated[int, Form()],
    enddate: Annotated[int, Form()],
    withings_repo: LocalWithingsRepository = Depends(get_withings_repository),
    slack_repo: RemoteSlackRepository = Depends(get_slack_repository),
):
    logging.info(
        "withings_notification_webhook: "
        + f"userid={userid}, startdate={startdate}, enddate={enddate}"
    )
    if last_processed_withings_notification_per_user.get(userid, None) != (
        startdate,
        enddate,
    ):
        try:
            await usecase_process_new_weight.do(
                withings_repo=withings_repo,
                slack_repo=slack_repo,
                withings_userid=userid,
                startdate=startdate,
                enddate=enddate,
            )
            last_processed_withings_notification_per_user[userid] = (
                startdate,
                enddate,
            )
        except UserLoggedOutException:
            await usecase_post_user_logged_out.do(
                withings_repo=withings_repo,
                slack_repo=slack_repo,
                withings_userid=userid,
            )
    else:
        logging.info("Ignoring duplicate withings notification")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
