import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.database import crud
from slackhealthbot.dependencies import get_db, templates
from slackhealthbot.services import slack
from slackhealthbot.services.exceptions import UserLoggedOutException
from slackhealthbot.services.oauth import oauth
from slackhealthbot.services.withings import api as withings_api
from slackhealthbot.services.withings import oauth as withings_oauth
from slackhealthbot.settings import settings

router = APIRouter()


@router.head("/withings-oauth-webhook/")
def validate_withings_oauth_webhook():
    return Response()


@router.head("/withings-notification-webhook/")
def validate_withings_notification_webhook():
    return Response()


@router.get("/withings-oauth-webhook/")
async def withings_oauth_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    token: dict = await oauth.fetch_token(withings_oauth.PROVIDER, request)
    user = await withings_oauth.update_token(
        db=db, token=token, slack_alias=request.session.pop("slack_alias")
    )
    await withings_api.subscribe(user)
    return templates.TemplateResponse(
        request=request, name="login_complete.html", context={"provider": "withings"}
    )


@router.get("/v1/withings-authorization/{slack_alias}")
async def get_withings_authorization(slack_alias: str, request: Request):
    return await oauth.create_oauth_url(
        provider=withings_oauth.PROVIDER,
        request=request,
        slack_alias=slack_alias,
        redirect_uri=settings.withings_redirect_uri,
    )


last_processed_withings_notification_per_user = {}


@router.post("/withings-notification-webhook/")
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
