import datetime

from slackhealthbot.domain.localrepository.localfitbitrepository import (
    LocalFitbitRepository,
    UserIdentity,
)
from slackhealthbot.domain.models.activity import (
    ActivityData,
    ActivityHistory,
    TopActivityStats,
)
from slackhealthbot.domain.remoterepository.remoteslackrepository import (
    RemoteSlackRepository,
)
from slackhealthbot.domain.usecases.fitbit import usecase_get_last_activity
from slackhealthbot.domain.usecases.slack import usecase_post_activity
from slackhealthbot.settings import settings


async def do(
    fitbit_repo: LocalFitbitRepository,
    slack_repo: RemoteSlackRepository,
    fitbit_userid: str,
    when: datetime.datetime,
) -> ActivityData | None:
    user_identity: UserIdentity = await fitbit_repo.get_user_identity_by_fitbit_userid(
        fitbit_userid=fitbit_userid,
    )
    new_activity = await usecase_get_last_activity.do(
        repo=fitbit_repo,
        fitbit_userid=fitbit_userid,
        when=when,
    )
    if not new_activity:
        return None

    activity_name, new_activity_data = new_activity

    if not await _is_new_valid_activity(
        fitbit_repo,
        fitbit_userid=fitbit_userid,
        type_id=new_activity_data.type_id,
        log_id=new_activity_data.log_id,
    ):
        return None

    last_activity_data: ActivityData = (
        await fitbit_repo.get_latest_activity_by_user_and_type(
            fitbit_userid=fitbit_userid,
            type_id=new_activity_data.type_id,
        )
    )

    await fitbit_repo.create_activity_for_user(
        fitbit_userid=fitbit_userid,
        activity=new_activity_data,
    )
    all_time_top_activity_stats: TopActivityStats = (
        await fitbit_repo.get_top_activity_stats_by_user_and_activity_type(
            fitbit_userid=fitbit_userid,
            type_id=new_activity_data.type_id,
        )
    )
    recent_top_activity_stats: TopActivityStats = (
        await fitbit_repo.get_top_activity_stats_by_user_and_activity_type(
            fitbit_userid=fitbit_userid,
            type_id=new_activity_data.type_id,
            since=datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=settings.fitbit_activity_record_history_days),
        )
    )
    await usecase_post_activity.do(
        repo=slack_repo,
        slack_alias=user_identity.slack_alias,
        activity_name=activity_name,
        activity_history=ActivityHistory(
            latest_activity_data=last_activity_data,
            new_activity_data=new_activity_data,
            all_time_top_activity_data=all_time_top_activity_stats,
            recent_top_activity_data=recent_top_activity_stats,
        ),
        record_history_days=settings.fitbit_activity_record_history_days,
    )

    return new_activity_data


async def _is_new_valid_activity(
    repo: LocalFitbitRepository,
    fitbit_userid: str,
    type_id: int,
    log_id: int,
) -> bool:
    return (
        type_id in settings.fitbit_activity_type_ids
        and not await repo.get_activity_by_user_and_log_id(
            fitbit_userid=fitbit_userid,
            log_id=log_id,
        )
    )
