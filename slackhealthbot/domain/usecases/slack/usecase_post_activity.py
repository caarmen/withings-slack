from slackhealthbot.domain.models.activity import (
    ActivityHistory,
    ActivityZone,
    Metric,
    Ranking,
)
from slackhealthbot.remoteservices.slack import messageapi


async def do(
    slack_alias: str,
    activity_history: ActivityHistory,
):
    activity = activity_history.new_activity_data
    zone_icons = {}
    if activity_history.latest_activity_data:
        duration_icon = get_activity_minutes_change_icon(
            activity.total_minutes.value
            - activity_history.latest_activity_data.total_minutes.value,
        )
        calories_icon = get_activity_calories_change_icon(
            activity.calories.value
            - activity_history.latest_activity_data.calories.value,
        )
        for zone_minutes in activity.zone_minutes:
            last_zone_minutes = next(
                (
                    x.minutes.value
                    for x in activity_history.latest_activity_data.zone_minutes
                    if x.zone == zone_minutes.zone
                ),
                0,
            )
            zone_icons[zone_minutes.zone] = get_activity_minutes_change_icon(
                zone_minutes.minutes.value - last_zone_minutes
            )

    else:
        duration_icon = calories_icon = ""
    message = f"""
New {activity.name} activity from <@{slack_alias}>:
    • Duration: {activity.total_minutes.value} minutes {duration_icon} {get_ranking_text(activity.total_minutes)}
    • Calories: {activity.calories.value} {calories_icon} {get_ranking_text(activity.calories)}
"""
    message += "\n".join(
        [
            f"    • {format_activity_zone(zone_minutes.zone)}"
            + f" minutes: {zone_minutes.minutes.value} "
            + zone_icons.get(zone_minutes.zone, "")
            + get_ranking_text(zone_minutes.minutes)
            for zone_minutes in activity.zone_minutes
        ]
    )
    await messageapi.post_message(message.strip())


def format_activity_zone(activity_zone: ActivityZone) -> str:
    return activity_zone.capitalize().replace("_", " ")


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


def get_ranking_text(metric: Metric) -> str:
    if metric.ranking == Ranking.ALL_TIME_TOP:
        return "New all-time recod! 🏆"
    if metric.ranking == Ranking.RECENT_TOP:
        return "New record! 🏆"  # TODO (x days)
    return ""
