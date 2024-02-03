import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from slackhealthbot.core.models import WeightData
from slackhealthbot.repositories import withingsrepository
from slackhealthbot.routers.dependencies import get_db, templates
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
        user: withingsrepository.User = (
            await withingsrepository.get_user_by_withings_userid(
                db,
                withings_userid=userid,
            )
        )
        try:
            last_weight_kg = await withings_api.get_last_weight_kg(
                oauth_token=user.oauth_data,
                startdate=startdate,
                enddate=enddate,
            )
        except UserLoggedOutException:
            await slack.post_user_logged_out(
                slack_alias=user.identity.slack_alias,
                service="withings",
            )
        else:
            if last_weight_kg:
                last_processed_withings_notification_per_user[userid] = (
                    startdate,
                    enddate,
                )
                await withingsrepository.update_user_weight(
                    db=db,
                    withings_userid=userid,
                    last_weight_kg=last_weight_kg,
                )
                await slack.post_weight(
                    WeightData(
                        weight_kg=last_weight_kg,
                        slack_alias=user.identity.slack_alias,
                        last_weight_kg=user.fitness_data.last_weight_kg,
                    )
                )
    else:
        logging.info("Ignoring duplicate withings notification")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
