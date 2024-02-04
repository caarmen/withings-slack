from slackhealthbot.core.models import ActivityData
from slackhealthbot.repositories import fitbitrepository


def core_activity_to_repository_activity(
    core: ActivityData | None,
) -> fitbitrepository.Activity | None:
    if not core:
        return None
    return fitbitrepository.Activity(
        log_id=core.log_id,
        total_minutes=core.total_minutes,
        calories=core.calories,
        type_id=core.type_id,
        **{f"{x.zone}_minutes": x.minutes for x in core.zone_minutes},
    )
