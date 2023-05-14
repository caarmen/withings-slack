import requests

import datetime
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


def format_minutes(total_minutes: int) -> str:
    hours, minutes_remainder = divmod(total_minutes, 60)
    return f"{hours}h {minutes_remainder}m" if hours else f"{minutes_remainder}m"


def format_time(input: datetime.datetime) -> str:
    return input.strftime("%-H:%M")


def post_sleep(sleep_data: SleepData):
    message = f"""
    New sleep from <@{sleep_data.slack_alias}>: 
    • Went to bed at {format_time(sleep_data.start_time)}
    • Woke up at {format_time(sleep_data.end_time)}
    • Total sleep: {format_minutes(sleep_data.sleep_minutes)}
    • Awake: {format_minutes(sleep_data.wake_minutes)}
    • Score: {sleep_data.score}
    """.strip()
    requests.post(
        url=settings.slack_webhook_url,
        json={
            "text": message,
        },
    )
