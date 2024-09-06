from slackhealthbot.domain.models.activity import DailyActivityHistory
from slackhealthbot.domain.remoterepository.remoteslackrepository import (
    RemoteSlackRepository,
)
from slackhealthbot.domain.usecases.slack.usecase_activity_message_formatter import (
    get_activity_calories_change_icon,
    get_activity_distance_km_change_icon,
    get_activity_minutes_change_icon,
    get_ranking_text,
)


async def do(
    repo: RemoteSlackRepository,
    slack_alias: str,
    activity_name: str,
    history: DailyActivityHistory,
    record_history_days: int,
):
    message = create_message(
        slack_alias=slack_alias,
        activity_name=activity_name,
        history=history,
        record_history_days=record_history_days,
    )
    await repo.post_message(message.strip())


def create_message(
    slack_alias: str,
    activity_name: str,
    history: DailyActivityHistory,
    record_history_days: int,
) -> str:
    if history.previous_daily_activity_stats:
        calories_icon = (
            get_activity_calories_change_icon(
                history.new_daily_activity_stats.sum_calories
                - history.previous_daily_activity_stats.sum_calories
            )
            if history.previous_daily_activity_stats.sum_calories
            else ""
        )
        distance_km_icon = (
            get_activity_distance_km_change_icon(
                (
                    history.new_daily_activity_stats.sum_distance_km
                    - history.previous_daily_activity_stats.sum_distance_km
                )
                * 100
                / history.new_daily_activity_stats.sum_distance_km,
            )
            if history.new_daily_activity_stats.sum_distance_km
            and history.previous_daily_activity_stats.sum_distance_km
            else ""
        )
        total_minutes_icon = get_activity_minutes_change_icon(
            history.new_daily_activity_stats.sum_total_minutes
            - history.previous_daily_activity_stats.sum_total_minutes,
        )
        fat_burn_minutes_icon = (
            get_activity_minutes_change_icon(
                history.new_daily_activity_stats.sum_fat_burn_minutes
                - history.previous_daily_activity_stats.sum_fat_burn_minutes,
            )
            if history.new_daily_activity_stats.sum_fat_burn_minutes
            and history.previous_daily_activity_stats.sum_fat_burn_minutes
            else ""
        )
        cardio_minutes_icon = (
            get_activity_minutes_change_icon(
                history.new_daily_activity_stats.sum_cardio_minutes
                - history.previous_daily_activity_stats.sum_cardio_minutes,
            )
            if history.new_daily_activity_stats.sum_cardio_minutes
            and history.previous_daily_activity_stats.sum_cardio_minutes
            else ""
        )
        peak_minutes_icon = (
            get_activity_minutes_change_icon(
                history.new_daily_activity_stats.sum_peak_minutes
                - history.previous_daily_activity_stats.sum_peak_minutes,
            )
            if history.new_daily_activity_stats.sum_peak_minutes
            and history.previous_daily_activity_stats.sum_peak_minutes
            else ""
        )
        out_of_zone_minutes_icon = (
            get_activity_minutes_change_icon(
                history.new_daily_activity_stats.sum_out_of_zone_minutes
                - history.previous_daily_activity_stats.sum_out_of_zone_minutes,
            )
            if history.new_daily_activity_stats.sum_out_of_zone_minutes
            and history.previous_daily_activity_stats.sum_out_of_zone_minutes
            else ""
        )
    else:
        calories_icon = distance_km_icon = total_minutes_icon = (
            fat_burn_minutes_icon
        ) = cardio_minutes_icon = peak_minutes_icon = out_of_zone_minutes_icon = ""

    calories_record_text = get_ranking_text(
        history.new_daily_activity_stats.sum_calories,
        history.all_time_top_daily_activity_stats.top_sum_calories,
        history.recent_top_daily_activity_stats.top_sum_calories,
        record_history_days=record_history_days,
    )

    distance_km_record_text = get_ranking_text(
        history.new_daily_activity_stats.sum_distance_km,
        history.all_time_top_daily_activity_stats.top_sum_distance_km,
        history.recent_top_daily_activity_stats.top_sum_distance_km,
        record_history_days=record_history_days,
    )

    total_minutes_record_text = get_ranking_text(
        history.new_daily_activity_stats.sum_total_minutes,
        history.all_time_top_daily_activity_stats.top_sum_total_minutes,
        history.recent_top_daily_activity_stats.top_sum_total_minutes,
        record_history_days=record_history_days,
    )

    fat_burn_minutes_record_text = get_ranking_text(
        history.new_daily_activity_stats.sum_fat_burn_minutes,
        history.all_time_top_daily_activity_stats.top_sum_fat_burn_minutes,
        history.recent_top_daily_activity_stats.top_sum_fat_burn_minutes,
        record_history_days=record_history_days,
    )

    cardio_minutes_record_text = get_ranking_text(
        history.new_daily_activity_stats.sum_cardio_minutes,
        history.all_time_top_daily_activity_stats.top_sum_cardio_minutes,
        history.recent_top_daily_activity_stats.top_sum_cardio_minutes,
        record_history_days=record_history_days,
    )

    peak_minutes_record_text = get_ranking_text(
        history.new_daily_activity_stats.sum_peak_minutes,
        history.all_time_top_daily_activity_stats.top_sum_peak_minutes,
        history.recent_top_daily_activity_stats.top_sum_peak_minutes,
        record_history_days=record_history_days,
    )

    out_of_zone_minutes_record_text = get_ranking_text(
        history.new_daily_activity_stats.sum_out_of_zone_minutes,
        history.all_time_top_daily_activity_stats.top_sum_out_of_zone_minutes,
        history.recent_top_daily_activity_stats.top_sum_out_of_zone_minutes,
        record_history_days=record_history_days,
    )

    message = f"""
New daily {activity_name} activity from <@{slack_alias}>:
    • Activity count: {history.new_daily_activity_stats.count_activities}
    • Total duration: {history.new_daily_activity_stats.sum_total_minutes} minutes {total_minutes_icon} {total_minutes_record_text}
    • Total calories: {history.new_daily_activity_stats.sum_calories} {calories_icon} {calories_record_text}
"""
    if history.new_daily_activity_stats.sum_distance_km:
        message += f"""    • Distance: {history.new_daily_activity_stats.sum_distance_km:.3f} km {distance_km_icon} {distance_km_record_text}
"""
    if history.new_daily_activity_stats.sum_fat_burn_minutes:
        message += f"""    • Total fat burn minutes: {history.new_daily_activity_stats.sum_fat_burn_minutes} {fat_burn_minutes_icon} {fat_burn_minutes_record_text}
"""
    if history.new_daily_activity_stats.sum_cardio_minutes:
        message += f"""    • Total cardio minutes: {history.new_daily_activity_stats.sum_cardio_minutes} {cardio_minutes_icon} {cardio_minutes_record_text}
"""
    if history.new_daily_activity_stats.sum_peak_minutes:
        message += f"""    • Total peak minutes: {history.new_daily_activity_stats.sum_peak_minutes} {peak_minutes_icon} {peak_minutes_record_text}
"""
    if history.new_daily_activity_stats.sum_out_of_zone_minutes:
        message += f"""    • Total out of zone minutes: {history.new_daily_activity_stats.sum_out_of_zone_minutes} {out_of_zone_minutes_icon} {out_of_zone_minutes_record_text}
"""

    return message
