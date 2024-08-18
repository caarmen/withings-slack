from slackhealthbot.domain.models.activity import ActivityZone


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


DISTANCE_CHANGE_PCT_SMALL = 15
DISTANCE_CHANGE_PCT_LARGE = 25


def get_activity_distance_km_change_icon(distance_km_change_pct: int) -> str:
    if distance_km_change_pct > DISTANCE_CHANGE_PCT_LARGE:
        return "⬆️"
    if distance_km_change_pct > DISTANCE_CHANGE_PCT_SMALL:
        return "↗️"
    if distance_km_change_pct < -DISTANCE_CHANGE_PCT_LARGE:
        return "⬇️"
    if distance_km_change_pct < -DISTANCE_CHANGE_PCT_SMALL:
        return "↘️"
    return "➡️"


def get_ranking_text(
    value: int,
    all_time_top_value: int,
    recent_top_value: int,
    record_history_days: int,
) -> str:
    if value and all_time_top_value and value >= all_time_top_value:
        return "New all-time record! 🏆"
    if value and recent_top_value and value >= recent_top_value:
        return f"New record (last {record_history_days} days)! 🏆"
    return ""
