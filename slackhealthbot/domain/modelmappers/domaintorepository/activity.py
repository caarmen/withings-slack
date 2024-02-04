from slackhealthbot.data.repositories import fitbitrepository
from slackhealthbot.domain.models.activity import ActivityData


def domain_activity_to_repository_activity(
    domain: ActivityData | None,
) -> fitbitrepository.Activity | None:
    if not domain:
        return None
    return fitbitrepository.Activity(
        log_id=domain.log_id,
        total_minutes=domain.total_minutes,
        calories=domain.calories,
        type_id=domain.type_id,
        **{f"{x.zone}_minutes": x.minutes for x in domain.zone_minutes},
    )
