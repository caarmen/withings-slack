from slackhealthbot.domain.models.weight import WeightData
from slackhealthbot.remoteservices.slack import messageapi


async def do(weight_data: WeightData):
    icon = _get_weight_change_icon(weight_data)
    message = (
        f"New weight from <@{weight_data.slack_alias}>: "
        + f"{weight_data.weight_kg:.2f} kg. {icon}"
    )
    await messageapi.post_message(message)


WEIGHT_CHANGE_KG_SMALL = 0.1
WEIGHT_CHANGE_KG_LARGE = 1


def _get_weight_change_icon(weight_data: WeightData) -> str:
    if not weight_data.last_weight_kg:
        return ""
    weight_change = weight_data.weight_kg - weight_data.last_weight_kg
    if weight_change > WEIGHT_CHANGE_KG_LARGE:
        return "⬆️"
    if weight_change > WEIGHT_CHANGE_KG_SMALL:
        return "↗️"
    if weight_change < -WEIGHT_CHANGE_KG_LARGE:
        return "⬇️"
    if weight_change < -WEIGHT_CHANGE_KG_SMALL:
        return "↘️"
    return "➡️"
