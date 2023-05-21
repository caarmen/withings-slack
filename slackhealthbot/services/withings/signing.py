import datetime
import hashlib
import hmac

import requests

from slackhealthbot.settings import settings


def create_signature(action: str, nonce: str) -> str:
    client_id = settings.withings_client_id
    data = f"{action},{client_id},{nonce}"
    return hmac.new(
        bytearray(settings.withings_client_secret.encode("utf-8")),
        bytearray(data.encode("utf-8")),
        digestmod=hashlib.sha256,
    ).hexdigest()


def get_nonce() -> str:
    action = "getnonce"
    timestamp = int(datetime.datetime.now().timestamp())
    signature = create_signature(action, timestamp)
    response = requests.post(
        f"{settings.withings_base_url}v2/signature/",
        data={
            "action": action,
            "client_id": settings.withings_client_id,
            "timestamp": timestamp,
            "signature": signature,
        },
    )
    response_content = response.json()
    return response_content["body"]["nonce"]


def sign_action(action: str) -> dict[str, str]:
    nonce = get_nonce()
    signature = create_signature(action, nonce)
    return {
        "nonce": nonce,
        "signature": signature,
    }
