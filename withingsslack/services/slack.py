import requests

from withingsslack.services.models import WeightData
from withingsslack.settings import settings


def post_weight(weight_data: WeightData):
    date_str = weight_data.date.strftime("%a %d %b %Y, %H:%M")
    message = (
        f"<@{weight_data.slack_alias}> weighed in at "
        + f"{weight_data.weight_kg:.2f} kg on {date_str}"
    )
    requests.post(
        url=settings.slack_webhook_url,
        json={
            "text": message,
        },
    )
