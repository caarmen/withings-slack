"""
I think this whole file is not needed
"""
import datetime
import hashlib
import hmac

import requests

from withingsslack.settings import settings


def _create_signature_request_payload() -> str:
    action = "getnonce"
    client_id = settings.withings_client_id
    timestamp = int(datetime.datetime.now().timestamp())
    data = f"{action},{client_id},{timestamp}"
    signature = hmac.new(
        bytearray(settings.withings_client_secret.encode("utf-8")),
        bytearray(data.encode("utf-8")),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return {
        "action": action,
        "client_id": client_id,
        "timestamp": timestamp,
        "signature": signature,
    }


def get_nonce() -> str:
    response = requests.post(
        f"{settings.withings_base_url}v2/signature/",
        data=_create_signature_request_payload(),
    )
    response_content = response.json()
    return response_content["body"]["nonce"]
