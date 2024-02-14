from slackhealthbot.domain.models.activity import ActivityHistory, ActivityZone
from slackhealthbot.remoteservices.slack import messageapi


async def do(
    slack_alias: str,
    activity_history: ActivityHistory,
    record_history_days: int,
):
    activity = activity_history.new_activity_data
    zone_icons = {}
    zone_record_texts = {}
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
    duration_record_text = get_ranking_text(
        activity.total_minutes,
        activity_history.all_time_top_activity_data.total_minutes,
        activity_history.recent_top_activity_data.total_minutes,
        record_history_days=record_history_days,
    )
    calories_record_text = get_ranking_text(
        activity.calories,
        activity_history.all_time_top_activity_data.calories,
        activity_history.recent_top_activity_data.calories,
        record_history_days=record_history_days,
    )
    for zone_minutes in activity.zone_minutes:
        all_time_top_value = next(
            (
                x.minutes
                for x in activity_history.all_time_top_activity_data.zone_minutes
                if x.zone == zone_minutes.zone
            ),
            0,
        )
        recent_top_value = next(
            (
                x.minutes
                for x in activity_history.recent_top_activity_data.zone_minutes
                if x.zone == zone_minutes.zone
            ),
            0,
        )
        zone_record_texts[zone_minutes.zone] = get_ranking_text(
            zone_minutes.minutes,
            all_time_top_value,
            recent_top_value,
            record_history_days=record_history_days,
        )
    message = f"""
New {activity.name} activity from <@{slack_alias}>:
    • Duration: {activity.total_minutes} minutes {duration_icon} {duration_record_text}
    • Calories: {activity.calories} {calories_icon} {calories_record_text}
"""
    message += "\n".join(
        [
            f"    • {format_activity_zone(zone_minutes.zone)}"
            + f" minutes: {zone_minutes.minutes} "
            + zone_icons.get(zone_minutes.zone, "")
            + f" {zone_record_texts.get(zone_minutes.zone, '')}"
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


def get_ranking_text(
    value: int,
    all_time_top_value: int,
    recent_top_value: int,
    record_history_days: int,
) -> str:
    if value >= all_time_top_value:
        return "New all-time record! 🏆"
    if value >= recent_top_value:
        return f"New record (last {record_history_days} days)! 🏆"
    return ""
