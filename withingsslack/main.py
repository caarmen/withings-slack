from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, Form, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from withingsslack import database
from withingsslack.database.connection import SessionLocal
from withingsslack.services import slack
from withingsslack.services.withings import api as withings_api
from withingsslack.services.withings import oauth as withings_oauth

database.init()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


@app.get("/v1/withings-authorization/{slack_alias}")
def get_withings_authorization(slack_alias: str):
    return RedirectResponse(
        url=withings_oauth.create_oauth_url(slack_alias=slack_alias)
    )


@app.head("/withings-oauth-webhook/")
def validate_withings_oauth_webhook():
    return Response()


@app.get("/withings-oauth-webhook/")
def withings_oauth_webhook(code: str, state: str, db: Session = Depends(get_db)):
    user = withings_oauth.fetch_token(db=db, state=state, code=code)
    withings_api.subscribe(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.head("/withings-notification-webhook/")
def validate_withings_notification_webhook():
    return Response()


@app.post("/withings-notification-webhook/")
def withings_notification_webhook(
    userid: Annotated[str, Form()],
    startdate: Annotated[int, Form()],
    enddate: Annotated[int, Form()],
    db: Session = Depends(get_db),
):
    last_weight_data = withings_api.get_last_weight(
        db,
        userid=userid,
        startdate=startdate,
        enddate=enddate,
    )
    if last_weight_data:
        slack.post_weight(last_weight_data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
