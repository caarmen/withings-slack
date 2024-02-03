import datetime

import httpx

from slackhealthbot.core.models import (
    ActivityHistory,
    ActivityZone,
    SleepData,
    WeightData,
)
from slackhealthbot.settings import settings


async def post_weight(weight_data: WeightData):
    icon = get_weight_change_icon(weight_data)
    message = (
        f"New weight from <@{weight_data.slack_alias}>: "
        + f"{weight_data.weight_kg:.2f} kg. {icon}"
    )
    async with httpx.AsyncClient() as client:
        await client.post(
            url=str(settings.slack_webhook_url),
            json={
                "text": message,
            },
        )


WEIGHT_CHANGE_KG_SMALL = 0.1
WEIGHT_CHANGE_KG_LARGE = 1


def get_weight_change_icon(weight_data: WeightData) -> str:
    if not weight_data.last_weight_kg:
        return ""
    weight_change = weight_data.weight_kg - weight_data.last_weight_kg
    if weight_change > WEIGHT_CHANGE_KG_LARGE:
        return "⬆️"
    if weight_change > WEIGHT_CHANGE_KG_SMALL:
        return "↗️"
    if weight_change < -WEIGHT_CHANGE_KG_LARGE:
        return "⬇️"
    if weight_change < -WEIGHT_CHANGE_KG_SMALL:
        return "↘️"
    return "➡️"


def format_minutes(total_minutes: int) -> str:
    hours, minutes_remainder = divmod(total_minutes, 60)
    return f"{hours}h {minutes_remainder}m" if hours else f"{minutes_remainder}m"


def format_time(input: datetime.datetime) -> str:
    return input.strftime("%-H:%M")


def format_activity_zone(activity_zone: ActivityZone) -> str:
    return activity_zone.name.capitalize().replace("_", " ")


SLEEP_TIME_SECONDS_CHANGE_SMALL = 15 * 60
SLEEP_TIME_SECONDS_CHANGE_LARGE = 45 * 60


def get_seconds_change_icon(seconds_change: int) -> str:
    if seconds_change > SLEEP_TIME_SECONDS_CHANGE_LARGE:
        return "⬆️"
    if seconds_change > SLEEP_TIME_SECONDS_CHANGE_SMALL:
        return "↗️"
    if seconds_change < -SLEEP_TIME_SECONDS_CHANGE_LARGE:
        return "⬇️"
    if seconds_change < -SLEEP_TIME_SECONDS_CHANGE_SMALL:
        return "↘️"
    return "➡️"


ACTIVITY_DURATION_MINUTES_CHANGE_SMALL = 2
ACTIVITY_DURATION_MINUTES_CHANGE_LARGE = 10


def get_activity_minutes_change_icon(minutes_change: int) -> str:
    if minutes_change > ACTIVITY_DURATION_MINUTES_CHANGE_LARGE:
        return "⬆️"
    if minutes_change > ACTIVITY_DURATION_MINUTES_CHANGE_SMALL:
        return "↗️"
    if minutes_change < -ACTIVITY_DURATION_MINUTES_CHANGE_LARGE:
        return "⬇️"
    if minutes_change < -ACTIVITY_DURATION_MINUTES_CHANGE_SMALL:
        return "↘️"
    return "➡️"


CALORIES_CHANGE_SMALL = 25
CALORIES_CHANGE_LARGE = 50


def get_activity_calories_change_icon(calories_change: int) -> str:
    if calories_change > CALORIES_CHANGE_LARGE:
        return "⬆️"
    if calories_change > CALORIES_CHANGE_SMALL:
        return "↗️"
    if calories_change < -CALORIES_CHANGE_LARGE:
        return "⬇️"
    if calories_change < -CALORIES_CHANGE_SMALL:
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
            url=str(settings.slack_webhook_url),
            json={
                "text": message,
            },
        )


async def post_activity(
    slack_alias: str,
    activity_history: ActivityHistory,
):
    activity = activity_history.new_activity_data
    zone_icons = {}
    if activity_history.latest_activity_data:
        duration_icon = get_activity_minutes_change_icon(
            activity.total_minutes
            - activity_history.latest_activity_data.total_minutes,
        )
        calories_icon = get_activity_calories_change_icon(
            activity.calories - activity_history.latest_activity_data.calories,
        )
        for zone_minutes in activity.zone_minutes:
            last_zone_minutes = next(
                (
                    x.minutes
                    for x in activity_history.latest_activity_data.zone_minutes
                    if x.zone == zone_minutes.zone
                ),
                0,
            )
            zone_icons[zone_minutes.zone] = get_activity_minutes_change_icon(
                zone_minutes.minutes - last_zone_minutes
            )

    else:
        duration_icon = calories_icon = ""
    message = f"""
New {activity.name} activity from <@{slack_alias}>:
    • Duration: {activity.total_minutes} minutes {duration_icon}
    • Calories: {activity.calories} {calories_icon}
"""
    message += "\n".join(
        [
            f"    • {format_activity_zone(zone_minutes.zone)}"
            + f" minutes: {zone_minutes.minutes} "
            + zone_icons.get(zone_minutes.zone, "")
            for zone_minutes in activity.zone_minutes
        ]
    )
    async with httpx.AsyncClient() as client:
        await client.post(
            url=str(settings.slack_webhook_url),
            json={
                "text": message.strip(),
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
            url=str(settings.slack_webhook_url),
            json={
                "text": message,
            },
        )
