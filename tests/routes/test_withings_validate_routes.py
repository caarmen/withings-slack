import pytest
from fastapi import status
from fastapi.testclient import TestClient


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=["webhook"],
    argvalues=[["/withings-oauth-webhook"], ["/withings-notification-webhook"]],
)
async def test_validate_withings_webhook(
    client: TestClient,
    webhook: str,
):
    # When we receive the callback from withings to validate the webhook
    response = client.head(webhook)

    assert response.status_code == status.HTTP_200_OK
