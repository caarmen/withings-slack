from slackhealthbot.data.repositories import fitbitrepository
from slackhealthbot.domain.models.activity import ActivityData


def domain_activity_to_repository_activity(
    domain: ActivityData,
) -> fitbitrepository.Activity:
    return fitbitrepository.Activity(
        log_id=domain.log_id,
        total_minutes=domain.total_minutes.value,
        calories=domain.calories.value,
        type_id=domain.type_id,
        **{f"{x.zone}_minutes": x.minutes.value for x in domain.zone_minutes},
    )
