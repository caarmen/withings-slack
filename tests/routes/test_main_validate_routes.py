import pytest
from fastapi import status
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_validate_root(
    client: TestClient,
):
    response = client.head("/")

    assert response.status_code == status.HTTP_200_OK
