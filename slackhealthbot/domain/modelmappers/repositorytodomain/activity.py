from slackhealthbot.data.repositories import fitbitrepository
from slackhealthbot.domain.models.activity import (
    ActivityData,
    ActivityZone,
    ActivityZoneMinutes,
    Metric,
    Ranking,
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
        calories=Metric(repo.calories, Ranking.NONE),
        total_minutes=Metric(repo.total_minutes, Ranking.NONE),
        zone_minutes=[
            ActivityZoneMinutes(
                zone=x,
                minutes=Metric(getattr(repo, f"{x}_minutes"), Ranking.NONE),
            )
            for x in ActivityZone
            if getattr(repo, f"{x}_minutes")
        ],
    )
