from slackhealthbot.domain.models.activity import ActivityHistory, ActivityZone
from slackhealthbot.remoteservices.slack import messageapi


async def do(
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
    await messageapi.post_message(message.strip())


def format_activity_zone(activity_zone: ActivityZone) -> str:
    return activity_zone.name.capitalize().replace("_", " ")


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
