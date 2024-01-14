import datetime
import hashlib
import hmac
import typing

import httpx
from authlib.common.urls import add_params_to_qs
from authlib.integrations.httpx_client import OAuth2ClientAuth
from authlib.integrations.httpx_client.utils import build_request

from slackhealthbot.settings import settings


class SignatureAuth(OAuth2ClientAuth):
    """
    https://developer.withings.com/api-reference/#tag/oauth2/operation/oauth2-getaccesstoken

    Withings supports two ways to retrieve access tokens:

    * "using secret."
      In this case, configuring token_endpoint_auth_method="client_secret_post"
      during OAuth.register() works. The client_secret is sent in the request body.

    * "using signature."
      In this case, we don't transmit the client_secret. Instead, we sign requests by
      retrieving a nonce from Withings, then creating a signature using hmac. It shares
      some similarities with OAuth1, but isn't really OAuth1 (so we can't use authlib
      OAuth1 apis).

    Passing auth=SignatureAuth(...) to authlib functions to perform requests will make
    it use the "using signature" protocol.
    """

    requires_response_body = True

    def __init__(self):
        super().__init__(
            client_id=settings.withings_client_id,
            client_secret=settings.withings_client_secret,
            auth_method="none",
        )

    def auth_flow(
        self, request: httpx.Request
    ) -> typing.Generator[httpx.Request, httpx.Response, None]:
        if request.url == f"{settings.withings_base_url}v2/oauth2":
            nonce_request = prepare_nonce_request()
            # https://docs.authlib.org/en/latest/client/api.html#authlib.integrations.httpx_client.OAuth1Auth.auth_flow
            nonce_response = yield nonce_request
            signed_request = sign_request(nonce_response, request)
            yield from super().auth_flow(signed_request)
        else:
            yield from super().auth_flow(request)


def create_signature(action: str, nonce: str) -> str:
    client_id = settings.withings_client_id
    data = f"{action},{client_id},{nonce}"
    return hmac.new(
        bytearray(settings.withings_client_secret.encode("utf-8")),
        bytearray(data.encode("utf-8")),
        digestmod=hashlib.sha256,
    ).hexdigest()


def prepare_nonce_request() -> httpx.Request:
    action = "getnonce"
    timestamp = int(datetime.datetime.now().timestamp())
    signature = create_signature(action, timestamp)
    return httpx.Request(
        "POST",
        f"{settings.withings_base_url}v2/signature/",
        data={
            "action": action,
            "client_id": settings.withings_client_id,
            "timestamp": timestamp,
            "signature": signature,
        },
    )


def sign_request(
    nonce_response: httpx.Response, request: httpx.Request
) -> httpx.Request:
    nonce = nonce_response.json()["body"]["nonce"]
    action = "requesttoken"
    content = add_params_to_qs(
        request.content,
        params={
            "nonce": nonce,
            "signature": create_signature(action, nonce),
            "action": action,
        },
    )
    return build_request(
        url=request.url,
        headers=request.headers,
        body=content,
        initial_request=request,
    )
