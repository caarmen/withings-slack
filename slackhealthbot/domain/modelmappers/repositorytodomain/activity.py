from slackhealthbot.data.repositories import fitbitrepository
from slackhealthbot.domain.models.activity import (
    ActivityData,
    ActivityZone,
    ActivityZoneMinutes,
)


def repository_activity_to_core_activity(
    repo: fitbitrepository.Activity | None,
    name: str,
) -> ActivityData | None:
    if not repo:
        return None
    return ActivityData(
        log_id=repo.log_id,
        type_id=repo.type_id,
        name=name,
        calories=repo.calories,
        total_minutes=repo.total_minutes,
        zone_minutes=[
            ActivityZoneMinutes(
                zone=x,
                minutes=getattr(repo, f"{x}_minutes"),
            )
            for x in ActivityZone
            if getattr(repo, f"{x}_minutes")
        ],
    )
