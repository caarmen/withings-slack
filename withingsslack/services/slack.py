import requests

from withingsslack.services.models import WeightData
from withingsslack.settings import settings


def post_weight(weight_data: WeightData):
    message = (
        f"New weight from <@{weight_data.slack_alias}>: "
        + f"{weight_data.weight_kg:.2f} kg."
    )
    requests.post(
        url=settings.slack_webhook_url,
        json={
            "text": message,
        },
    )
