import requests

from withingsslack.services.models import WeightData, SleepData
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


def _format_minutes(total_minutes: int) -> str:
    hours, minutes_remainder = divmod(total_minutes, 60)
    return f"{hours}h {minutes_remainder}m"


def post_sleep(sleep_data: SleepData):
    message = f"""
    New sleep from <@{sleep_data.slack_alias}>: 
    • Total sleep: {_format_minutes(sleep_data.total_sleep_minutes)}.
    • Rem sleep: {_format_minutes(sleep_data.rem_minutes)}.
    • Light sleep: {_format_minutes(sleep_data.light_minutes)}.
    • Deep sleep: {_format_minutes(sleep_data.deep_minutes)}.
    • Awake: {_format_minutes(sleep_data.wake_minutes)}.
    """.strip()
    requests.post(
        url=settings.slack_webhook_url,
        json={
            "text": message,
        },
    )
