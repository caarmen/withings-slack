from slackhealthbot.data.repositories import fitbitrepository
from slackhealthbot.domain.models.activity import (
    ActivityData,
    ActivityZone,
    ActivityZoneMinutes,
)


def repository_activity_to_domain_activity(
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


def repository_top_activity_stats_to_domain_activity(
    repo: fitbitrepository.TopActivityStats,
    name: str,
) -> ActivityData:
    return ActivityData(
        log_id=-1,
        type_id=-1,
        name=name,
        calories=repo.top_calories,
        total_minutes=repo.top_total_minutes,
        zone_minutes=[
            ActivityZoneMinutes(
                zone=x,
                minutes=getattr(repo, f"top_{x}_minutes"),
            )
            for x in ActivityZone
            if hasattr(repo, f"top_{x}_minutes") and getattr(repo, f"top_{x}_minutes")
        ],
    )
