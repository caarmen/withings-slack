import datetime

import httpx

from slackhealthbot.services.models import SleepData, WeightData
from slackhealthbot.settings import settings


async def post_weight(weight_data: WeightData):
    icon = get_weight_change_icon(weight_data)
    message = (
        f"New weight from <@{weight_data.slack_alias}>: "
        + f"{weight_data.weight_kg:.2f} kg. {icon}"
    )
    async with httpx.AsyncClient() as client:
        await client.post(
            url=settings.slack_webhook_url,
            json={
                "text": message,
            },
        )


def get_weight_change_icon(weight_data: WeightData) -> str:
    if not weight_data.last_weight_kg:
        return ""
    weight_change = weight_data.weight_kg - weight_data.last_weight_kg
    if weight_change > 1:
        return "⬆️"
    if weight_change > 0.1:
        return "↗️"
    if weight_change < -1:
        return "⬇️"
    if weight_change < -0.1:
        return "↘️"
    return "➡️"


def format_minutes(total_minutes: int) -> str:
    hours, minutes_remainder = divmod(total_minutes, 60)
    return f"{hours}h {minutes_remainder}m" if hours else f"{minutes_remainder}m"


def format_time(input: datetime.datetime) -> str:
    return input.strftime("%-H:%M")


def get_seconds_change_icon(seconds_change: int) -> str:
    if seconds_change > 45 * 60:
        return "⬆️"
    if seconds_change > 15 * 60:
        return "↗️"
    if seconds_change < -45 * 60:
        return "⬇️"
    if seconds_change < -15 * 60:
        return "↘️"
    return "➡️"


def get_datetime_change_icon(
    last_datetime: datetime.datetime, new_datetime: datetime.datetime
) -> str:
    if last_datetime == new_datetime:
        return "➡️"

    fake_last_datetime = last_datetime + datetime.timedelta(days=1)
    time_diff_seconds = int((new_datetime - fake_last_datetime).total_seconds())
    return get_seconds_change_icon(time_diff_seconds)


async def post_sleep(
    slack_alias: str,
    new_sleep_data: SleepData,
    last_sleep_data: SleepData,
):
    if last_sleep_data:
        start_time_icon = get_datetime_change_icon(
            last_datetime=last_sleep_data.start_time,
            new_datetime=new_sleep_data.start_time,
        )
        end_time_icon = get_datetime_change_icon(
            last_datetime=last_sleep_data.end_time,
            new_datetime=new_sleep_data.end_time,
        )
        sleep_minutes_icon = get_seconds_change_icon(
            (new_sleep_data.sleep_minutes - last_sleep_data.sleep_minutes) * 60
        )
        wake_minutes_icon = get_seconds_change_icon(
            (new_sleep_data.wake_minutes - last_sleep_data.wake_minutes) * 60
        )
    else:
        start_time_icon = end_time_icon = sleep_minutes_icon = wake_minutes_icon = ""

    message = f"""
    New sleep from <@{slack_alias}>: 
    • Went to bed at {format_time(new_sleep_data.start_time)} {start_time_icon}
    • Woke up at {format_time(new_sleep_data.end_time)} {end_time_icon}
    • Total sleep: {format_minutes(new_sleep_data.sleep_minutes)} {sleep_minutes_icon}
    • Awake: {format_minutes(new_sleep_data.wake_minutes)} {wake_minutes_icon}
    """.strip()
    async with httpx.AsyncClient() as client:
        await client.post(
            url=settings.slack_webhook_url,
            json={
                "text": message,
            },
        )


async def post_user_logged_out(slack_alias: str, service: str):
    message = f"""
Oh no <@{slack_alias}>, looks like you were logged out of {service}! 😳.
You'll need to log in again to get your reports:
{settings.server_url}v1/{service}-authorization/{slack_alias}
"""
    async with httpx.AsyncClient() as client:
        await client.post(
            url=settings.slack_webhook_url,
            json={
                "text": message,
            },
        )
